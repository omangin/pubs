import os
import re
import shutil
import subprocess
import collections

from ... import repo
from ... import files

from ...uis import get_ui
from ...configs import config
from ...plugins import PapersPlugin
from ...events import RemoveEvent, RenameEvent, AddEvent
from ...commands.helpers import add_references_argument, parse_reference

from .autofill_tools import autofill, replace_pattern


SECTION = 'texnote'
DIR = os.path.join(config().papers_dir, 'texnote')
TPL_DIR = os.path.join(DIR, 'template')
TPL_BODY = os.path.join(TPL_DIR, 'body.tex')
TPL_STYLE = os.path.join(TPL_DIR, 'style.sty')
TPL_BIB = os.path.join(TPL_DIR, 'bib.bib')

DFT_BODY = os.path.join(os.path.dirname(__file__), 'default_body.tex')
DFT_STYLE = os.path.join(os.path.dirname(__file__), 'default_style.sty')

STYLE_PATTERN = '\\usepackage{INFO}'
STYLE_INFO = os.path.splitext(TPL_STYLE)[0].replace(DIR, '')[1:]
BIB_PATTERN = '\\bibliography{INFO}'
BIB_INFO = os.path.splitext(TPL_BIB)[0].replace(DIR, '')[1:]
BIBSTYLE_PATTERN = '\\bibliographystyle{INFO}'
DFT_BIBSTYLE_INFO = 'ieeetr'

class TexnotePlugin(PapersPlugin):

    def __init__(self):
        self.name = SECTION

        self.texcmds = collections.OrderedDict([
                        ('remove', self.remove),
                        ('edit', self.edit),
                        ('edit_template', self.edit_template),
                        ('generate_bib', self.generate_bib),
                        ('clean', self.clean),
                        ])

    def _ensure_init(self):
        if not files.check_directory(DIR):
            os.mkdir(DIR)
        if not files.check_directory(TPL_DIR):
            os.mkdir(TPL_DIR)
        if not files.check_file(TPL_BODY):
            shutil.copy(DFT_BODY, TPL_BODY)
        if not files.check_file(TPL_STYLE):
            shutil.copy(DFT_STYLE, TPL_STYLE)
        if not files.check_file(TPL_BIB):
            self.generate_bib()

    def parser(self, subparsers):
        parser = subparsers.add_parser(self.name, help='edit advance note in latex')
        sub = parser.add_subparsers(title='valid texnote commands', dest='texcmd')
        # remove
        p = sub.add_parser('remove', help='remove a reference')
        add_references_argument(p, single=True)
        # edit
        p = sub.add_parser('edit', help='edit the reference texnote')
        p.add_argument('-v', '--view', action='store_true',
                help='open the paper in a pdf viewer', default=False)
        p.add_argument('-w', '--with', dest='with_command', default=None,
                       help='command to use to open the file')
        add_references_argument(p, single=True)
        # edit_template
        p = sub.add_parser('edit_template',
                           help='edit the latex template used by texnote')
        p.add_argument('-w', '--with', dest='with_command', default=None,
                       help='command to use to open the file')
        p.add_argument('-B', '--body', action='store_true',
                help='edit the main body', default=False)
        p.add_argument('-S', '--style', action='store_true',
                help='open the style', default=False)
        # generate_bib
        p = sub.add_parser('generate_bib',
                           help='generate the latex bib used by texnote')
        # clean
        p = sub.add_parser('clean',
                           help='delete all but tex files in the texnote folder')
        p.add_argument('-f', '--force', action='store_true',
                       help='do not ask for confirmation', default=False)
        return parser

    def command(self, args):
        self._ensure_init()

        texcmd = args.texcmd
        del args.texcmd
        self.texcmds[texcmd](**vars(args))

    def _texfile(self, citekey):
        return os.path.join(DIR, citekey + '.tex')

    def _ensure_texfile(self, citekey):
        if not files.check_file(self._texfile(citekey)):
            shutil.copy(TPL_BODY, self._texfile(citekey))

    def get_bib_style(self):
        default = DFT_BIBSTYLE_INFO
        return config(SECTION).get('bib_style', default)

    def _autofill_texfile(self, citekey):
        with open(self._texfile(citekey)) as f:
            text = f.read()
        rp = repo.Repository(config())
        if citekey in rp:
            paper = rp.get_paper(citekey)
            text = autofill(text, paper)
            text = replace_pattern(text, STYLE_PATTERN, STYLE_INFO)
            text = replace_pattern(text, BIB_PATTERN, BIB_INFO)
            text = replace_pattern(text, BIBSTYLE_PATTERN, self.get_bib_style())
            with open(self._texfile(citekey), "w") as f:
                f.write(text)

    def get_texfile(self, citekey, autofill=False):
        """ This function returns the name of the texfile and
        ensure it exist and it is filled with info from the bibfile if possible"""
        self._ensure_texfile(citekey)
        if autofill:
            self._autofill_texfile(citekey)
        return self._texfile(citekey)

    def get_edit_cmd(self):
        default = config().edit_cmd
        return config(SECTION).get('edit_cmd', default)

    def edit(self, reference, view=False, with_command=None):
        if view:
            subprocess.Popen(['papers', 'open', reference])
        if with_command is None:
            with_command = self.get_edit_cmd()

        rp = repo.Repository(config())
        citekey = parse_reference(rp, reference)
        files.edit_file(with_command,
                        self.get_texfile(citekey, autofill=True),
                        temporary=False)

    def edit_template(self, body=False, style=False, with_command=None):
        if with_command is None:
            with_command = self.get_edit_cmd()
        if body:
            files.edit_file(with_command, TPL_BODY, temporary=False)
        if style:
            files.edit_file(with_command, TPL_STYLE, temporary=False)

    def create(self, citekey):
        self._autofill_texfile(citekey)

    def remove(self, reference):
        rp = repo.Repository(config())
        citekey = parse_reference(rp, reference)
        os.remove(self.get_texfile(citekey))

    def rename(self, old_citekey, new_citekey, overwrite=False):
        shutil.move(self.get_texfile(old_citekey), self.get_texfile(new_citekey))

    def generate_bib(self):
        cmd = 'papers list -k |xargs papers export >> {}'.format(TPL_BIB)
        os.system(cmd)

    def clean(self, force=False):
        for f in os.listdir(DIR):
            path = os.path.join(DIR, f)
            if os.path.isfile(path):
                name, extension = os.path.splitext(path)
                if extension != '.tex':
                    if not force:
                        ui = get_ui()
                        are_you_sure = 'Are you sure you want to delete file [{}]'.format(path)
                        sure = ui.input_yn(question=are_you_sure, default='n')
                    if force or sure:
                        os.remove(path)




@AddEvent.listen()
def create(addevent):
    texplug = TexnotePlugin.get_instance()
    texplug.create(addevent.citekey)


@RemoveEvent.listen()
def remove(rmevent):
    texplug = TexnotePlugin.get_instance()
    texplug.remove(rmevent.citekey)


@RenameEvent.listen()
def rename(renamevent):
    texplug = TexnotePlugin.get_instance()
    texplug.rename(renamevent.old_citekey,
                   renamevent.paper.citekey,
                   overwrite=True)
