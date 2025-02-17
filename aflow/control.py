"""Functions for controlling high-level search functionality for the
AFLOW database.
"""
# server = "http://aflowlib.duke.edu/search/API/?"

# New server address which will be compatible with other interfaces like optimade
server = "http://aflowlib.org/API/aflux/?"
"""str: API server address over HTTP.
"""

from aflow import msg
from aflow.logic import _expr_to_strings
from aflow.keywords import all_keywords


def _check_input(string):
    """Check if the input string contains invalid string"""
    forbidden_chars = (
        '"',
        "@",
        "\\",
        "~",
        "/",
    )  # characters that will cause LUX crash
    if any([c in string for c in forbidden_chars]):
        msg.err(
            f"Input {string} contains one or more of the forbidden characters: {forbidden_chars}"
        )
        return False
    else:
        return True


def search(catalog=None, batch_size=100):
    """Returns a :class:`aflow.control.Query` to help construct the search
    query.

    Args:
        catalog (str): one of the catalogs supported on AFLOW: ['icsd', 'lib1',
          'lib2', 'lib3']. Also supports a `list` of catalog names.
        batch_size (int): number of data entries to return per HTTP request.
    """
    return Query(catalog, batch_size)


class Query(object):
    """Represents a search againts the AFLUX API.

    Args:
        catalog (str): one of the catalogs supported on AFLOW: ['icsd', 'lib1',
          'lib2', 'lib3']. Also supports a `list` of catalog names.
        batch_size (int): number of data entries to return per HTTP request.
        step (int): step size over entries.

    Attributes:
        filters (list): of `str` filter arguments to pass to the matchbook
          section of the API request.
        select (list): of :class:`aflow.keywords.Keyword` to *include* in the request.
        excludes (list): of :class:`aflow.keywords.Keyword` to *exclude* in the request.
        orderby (str): name of the keyword to order by. AFLUX only supports a
          single order-by parameter for now.
        catalog (str): one of the catalogs supported on AFLOW: ['icsd', 'lib1',
          'lib2', 'lib3']. Also supports a `list` of catalog names.
        N (int): number of results in the current search query.
        reverse (bool): when True, reverse the order of the results in the
          query.
        k (int): number of datasets per page for the current iterator. Can be
          controlled by `batch_size`.
        responses (dict): keys are (n,k) tuples from the pagination; values are
          the corresponding JSON dictionaries.
        step (int): step size over entries.
    """

    def __init__(self, catalog=None, batch_size=100, step=1):
        self.filters = []
        self.selects = []
        self.excludes = []
        self.order = None
        self.catalog = (
            catalog if isinstance(catalog, (list, tuple, type(None))) else [catalog]
        )
        self._N = None
        """int: number of results in the current search query."""
        self.reverse = False
        self._n = 1
        self.k = batch_size
        self.step = step
        self.responses = {}
        self._iter = 0
        """int: current integer id of the iterator in the *whole* dataset; this
        means it can have a value greater than :attr:`k`.
        """
        self._max_entry = None
        """int: index of the maximum entry that should be returned from this
        query.
        """
        self._matchbook = None
        """str: matchbook portion of the request URL.
        """
        self._final = False
        """bool: when True, this query is finalized and no additional filters,
        etc. can be added to it.
        """

    def reset_iter(self):
        """Resets the iterator back to zero so that the collection can be
        iterated over again *without* needing to request the data from the
        server again.
        """
        # TODO: confirm or remove
        self._iter = 0

    @property
    def n(self):
        """Current page number for the iterator."""
        if self.reverse:
            return -1 * self._n
        else:
            return self._n

    @property
    def N(self):
        if self._N is None:
            self._request(self.n, self.k)
        return self._N

    @property
    def max_N(self):
        """Returns the maximum integer index that will be reached by this query."""
        if self._max_entry is None:
            return self.N
        else:
            return self._max_entry

    def __len__(self):
        return self.max_N

    def __getitem__(self, seq):
        # We need to trigger the first request to make sure that the total
        # number of entries is fixed on the parent object, and so that the
        # pointers to the response caching are all the same.
        assert len(self) > 0

        from copy import copy

        result = copy(self)

        if type(seq) is slice:
            # Perform a shallow copy so that we get a new reference for the
            # indices.
            result._iter = seq.start if seq.start is not None else 0
            result._max_entry = seq.stop
            result.step = seq.step
            return result
        elif isinstance(seq, int):
            result._iter = seq
            return next(result)

    def _request(self, n, k):
        """Constructs the query string for this :class:`Query` object for the
        specified paging limits and then returns the response from the REST API
        as a python object.

        Args:
            n (int): page number of the results to return.
            k (int): number of datasets per page.
        """
        if len(self.responses) == 0:
            # We are making the very first request, finalize the query.
            self.finalize()

        import json

        from six.moves import urllib

        urlopen = urllib.request.urlopen
        # More robust handling, matchbook can be empty
        _matchbook = self.matchbook()
        if _matchbook != "":
            _matchbook = _matchbook + ","
        url = "{0}{1}{2}".format(server, _matchbook, self._directives(n, k))
        rawresp = urlopen(url).read().decode("utf-8")
        try:
            response = json.loads(rawresp)
        except:  # pragma: no cover
            # We can't easily simulate network failure...
            self._N = 0
            msg.err("API request fails for {}\n\n{}".format(url, rawresp))
            return

        if not response:
            self._N = 0
            msg.err(
                "Empty response from API. "
                "Check your query filters.\nURI: {}".format(url)
            )
            return
        # If this is the first request, then save the number of results in the
        # query.
        if len(self.responses) == 0:
            self._N = int(next(iter(response.keys())).split()[-1])
        self.responses[n] = response

    def reset(self):
        """Convenient way to reset the query results etc.
        this is a stateless method, does not return a Query instance
        """
        self.__init__(self.catalog, self.k, self.step)

    def finalize(self):
        """Finalize the query matchbook once all query strings are fixed"""
        # Generate the matchbook query, this has all the filters, selects and
        # ordering information.
        self.matchbook()
        # Switch out all of the keyword instances for their string
        # representations.
        # All of these are keywords
        self.selects = [str(s) for s in self.selects]
        # self.selects = _extract_keywords(self.selects)
        # parse the filters and extract known keywords
        self.filters = [str(f) for f in self.filters]
        self.excludes = [str(x) for x in self.excludes]
        self.order = str(self.order) if self.order is not None else None
        # Set the finalizer flag so that this object doesn't allow mutations.
        self._final = True

    def set_manual_matchbook(self, matchbook):
        """Statelessly set the matchbook string part of the aflow query
        set the self._matchbook to matchbook and make it final
        matchbook should be a string.

        The method does not enforce type check.
        Use it only when the default keyword method messes up
        """
        if not isinstance(matchbook, str):
            msg.err(
                (
                    f"Manual input query must be a string, not {type(matchbook)}."
                    "The matchbook is not set"
                )
            )
            self._matchbook = None
            self._final = False
            return self

        if _check_input(matchbook):
            self._matchbook = matchbook
            self._final = True
        else:
            self._matchbook = None

        return self

    def matchbook(self):
        """Constructs the matchbook portion of the query."""
        if not self._final:
            items = []
            # AFLUX orders by the first element in the query. If we have an orderby
            # specified, then place it first.
            if self.order is not None:
                # TODO: update the exclude keyword lists
                excludes = [x.name for x in self.excludes]
                selects = [v.name for v in self.selects]
                if self.order.name in excludes:
                    items.append("${}".format(str(self.order.name)))
                    idx = excludes.index(self.order.name)
                    self.excludes.pop(idx)
                else:
                    items.append(str(self.order.name))

                if self.order.name in selects:
                    idx = selects.index(self.order.name)
                    self.selects.pop(idx)

            items.extend(list(map(str, self.selects)))
            items.extend(list(map(str, self.filters)))
            items.extend(["${}".format(str(k)) for k in self.excludes])
            self._matchbook = ",".join(items)

        return self._matchbook

    def _directives(self, n, k):
        """Returns the directives portion of the AFLUX query.

        Args:
            n (int): page number of the results to return.
            k (int): number of datasets per page.
        """
        items = []
        if self.catalog is not None:
            items.append("catalog({})".format(":".join(self.catalog)))

        # Next, add the paging context. This query maintains its own paging
        # context
        items.append("paging({0:d},{1:d})".format(n, k))
        return ",".join(items)

    def __iter__(self):
        return self

    def next(self):  # pragma: no cover
        """Yields a generator over AFLUX API request results."""
        return self.__next__()

    def __next__(self):
        """Yields a generator over AFLUX API request results."""
        # First, find out which entry we are on.
        n = (self._iter // self.k) + 1
        i = self._iter % self.k

        # Reverse the sign now that we have figured out the ordinal page number.
        if self.reverse:
            n *= -1

        if self._iter < self.max_N and n not in self.responses:
            self._n = abs(n)
            self._request(self.n, self.k)

        assert len(self.responses) > 0

        from aflow.entries import Entry

        if self._iter < self.max_N:
            index = self.k * (abs(n) - 1) + i + 1
            key = "{} of {}".format(index, self.N)
            raw = self.responses[n][key]
            result = Entry(**raw)

            # Increment the iterator right before we return the entry.
            self._iter += 1
            return result
        else:
            raise StopIteration()

    def _final_check(self):
        """Checks whether this object is finalized; if it is, print a friendly
        message and return False, otherwise True.
        """
        if self._final:
            msg.info(
                "This query has been finalized. It cannot be mutated. "
                "Create a new query to change the matchbook."
            )
        return not self._final

    def filter(self, keyword):
        """Adds a search term to the current filter list. Calling :meth:`filter`
        multiple times will join the final filters together using logical *and*.

        Args:
            keyword (aflow.keywords.Keyword): that encapsulates the AFLUX
              request language logic.

        New version: allowing keyword as a single string containing filters
        """

        if self._final_check():
            self._N = None
            if isinstance(keyword, str):  # normal string
                if _check_input(keyword):
                    self.filters.append(keyword)
            elif hasattr(keyword, "func"):  # Is a sympy symbol
                expr = _expr_to_strings(keyword)
                self.filters.append(expr)
            else:
                msg.err(
                    (
                        "Query.filter() takes either "
                        "boolean expression or string,"
                        f" not {type(keyword)}"
                    )
                )
        return self

    def select(self, *keywords):
        """Adds a keyword to the list of properties to return for each material
        in the request.

        Args:
            keywords (list): of :class:`aflow.keywords.Keyword` that
              encapsulates the AFLUX request language logic.
        """
        if self._final_check():
            self._N = None
            for keyword in keywords:
                if keyword is not self.order:
                    self.selects.append(keyword)
        return self

    def orderby(self, keyword, reverse=False):
        """Sets a keyword to be the one by which

        Args:
            keyword (aflow.keywords.Keyword): that encapsulates the AFLUX
              request language logic.
            reverse (bool): when True, reverse the ordering.
        """
        if self._final_check():
            self._N = None
            self.order = keyword
            self.reverse = reverse
        return self

    def exclude(self, *keywords):
        """Sets a keyword to be *excluded* from the response.

        Args:
            keywords (list): of :class:`aflow.keywords.Keyword` that
              encapsulates the AFLUX request language logic.
        """
        if self._final_check():
            self._N = None
            for keyword in keywords:
                self.excludes.append(keyword)
        return self
