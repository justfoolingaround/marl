"""
Sphinx Inventory Reader
"""

from functools import cached_property
import io
import zlib

import regex


SPHINX_INVENTORY_RE = regex.compile(br'(?x)(.+?)\s+(\S*:\S*)\s+(-?\d+)\s+(\S+)\s+(.*)')

class SphinxInventoryIO(io.BytesIO):
    ENCODING = 'utf-8'

    BUFFER_SIZE = 16384

    start = 0

    inventory_version: 'int' = None
    project_name: 'str' = None
    project_version: 'str' = None
    
    source: 'str' = None

    def __init__(self, initial_bytes: bytes, source):
        self.decompressor = zlib.decompressobj()
        self.source = source        
        super().__init__(initial_bytes)

        inv = self.readline()

        if not inv.startswith(b'# Sphinx inventory version'):
            raise ValueError('Not a valid Sphinx inventory file')

        self.inventory_version = int(inv.split()[-1].decode(self.ENCODING).strip())

        self.project_name = self.readline()[11:].decode(self.ENCODING).strip()
        self.project_version = self.readline()[11:].decode(self.ENCODING).strip()

        if self.readline() != b'# The remainder of this file is compressed using zlib.\n':
            raise ValueError('Unsupported file format')

        self.start = self.tell()

    def iter_decompressed_chunks(self):
        """
        Iterate over the decompressed chunks of data.
        """
        
        self.seek(self.start)

        chunk = None
        while chunk != b'':
            chunk = self.read(self.BUFFER_SIZE)
            yield self.decompressor.decompress(chunk)
        yield self.decompressor.flush()
    
    def iter_decompressed_chunklines(self):
        """
        Iterate over the decompressed lines of data.
        """

        for chunk in self.iter_decompressed_chunks():
            while b'\n' in chunk:
                line, chunk = chunk.split(b'\n', 1)
                yield line
            else:
                yield chunk
    
    @classmethod
    async def get_inventory(cls, session, rtfm_url: 'str'):
        """
        Get the inventory from the given URL.
        """
        if not rtfm_url.endswith('/objects.inv'):
            rtfm_url = rtfm_url.rstrip('/') + '/objects.inv'

        return cls((await session.get(rtfm_url)).content, source=rtfm_url[:-12])
    
    def iter_entries(self):
        """
        Iterate over the entries in the inventory.
        """

        for line in self.iter_decompressed_chunklines():
            match = SPHINX_INVENTORY_RE.match(line)

            if match is None:
                continue

            name, directive, prio, location, display_name = match.groups()
            domain, _, subdirective = directive.partition(b":")

            if directive == b"std:doc":
                subdirective = b"label"

            if location.endswith(b"$"):
                location = location[:-1] + name

            yield ("{}:".format(subdirective.decode(self.ENCODING)) if domain == b'std' else '') + (name if display_name == b'-' else display_name).decode(self.ENCODING), location.decode(self.ENCODING)

    @cached_property
    def entries(self):
        return list(self.iter_entries())

    def search(self, query):
        
        for entry, location in self.entries:
            if query in entry:
                yield entry, location
