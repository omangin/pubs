
from . import databroker

class DataCache(object):
    """ DataCache class, provides a very similar interface as DataBroker

        Has two roles :
        1. Provides a buffer between the commands and the hard drive.
           Until a command request a hard drive ressource, it does not touch it.
        2. Keeps an up-to-date, pickled version of the repository, to speed up things
           when they are a lot of files. Update are also done only when required.
           Changes are detected using data modification timestamps.

        For the moment, only (1) is implemented.
    """
    def __init__(self, directory, create=False):
        self.directory = directory
        self._databroker = None
        if create:
            self._create()

    @property
    def databroker(self):
        if self._databroker is None:
            self._databroker = databroker.DataBroker(self.directory, create=False)
        return self._databroker

    def _create(self):
        self._databroker = databroker.DataBroker(self.directory, create=True)

    def pull_metadata(self, citekey):
        return self.databroker.pull_metadata(citekey)

    def pull_bibentry(self, citekey):
        return self.databroker.pull_bibentry(citekey)

    def push_metadata(self, citekey, metadata):
        self.databroker.push_metadata(citekey, metadata)

    def push_bibentry(self, citekey, bibdata):
        self.databroker.push_bibentry(citekey, bibdata)

    def push(self, citekey, metadata, bibdata):
        self.databroker.push(citekey, metadata, bibdata)

    def remove(self, citekey):
        self.databroker.remove(citekey)

    def exists(self, citekey, meta_check=False):
        return self.databroker.exists(citekey, meta_check=meta_check)

    def citekeys(self):
        return self.databroker.citekeys()

    def listing(self, filestats=True):
        return self.databroker.listing(filestats=filestats)

    def verify(self, bibdata_raw):
        return self.databroker.verify(bibdata_raw)

    # docbroker

    def in_docsdir(self, docpath):
        return self.databroker.in_docsdir(docpath)

    def real_docpath(self, docpath):
        return self.databroker.real_docpath(docpath)

    def add_doc(self, citekey, source_path, overwrite=False):
        return self.databroker.add_doc(citekey, source_path, overwrite=overwrite)

    def remove_doc(self, docpath, silent=True):
        return self.databroker.remove_doc(docpath, silent=silent)

    def rename_doc(self, docpath, new_citekey):
        return self.databroker.rename_doc(docpath, new_citekey)

    # notesbroker

    def real_notepath(self, citekey):
        return self.databroker.real_notepath(citekey)

    def remove_note(self, citekey, silent=True):
        return self.databroker.remove_note(citekey, silent=True)

    def rename_note(self, old_citekey, new_citekey):
        return self.databroker.rename_note(old_citekey, new_citekey)


# class ChangeTracker(object):

#     def __init__(self, cache, directory):
#         self.cache = cache
#         self.directory = directory

#     def changes(self):
#         """ Returns the list of modified files since the last cache was saved to disk"""
#         pass
