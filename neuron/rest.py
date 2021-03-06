import Cookie

from beaker.session import Session, SessionObject

from tornado.web import RequestHandler as _RequestHandler
from tornado.wsgi import WSGIContainer

from .ot import RedisTextDocumentBackend


class RequestHandler(_RequestHandler):
    def __init__(self, *args, **kwargs):
        _RequestHandler.__init__(self, *args, **kwargs)

        self.environ = WSGIContainer.environ(self.request)


class DocumentMetaHandler(RequestHandler):
    def get(self, doc_id):
        doc_id = int(doc_id)

        doc = self.application.get_document_backend(doc_id)
        rev, content = doc.get_latest()

        self.finish({
            "id": doc_id,
            "latest_rev": rev,
            "latest_content": content
        })


class DocumentRevisionHandler(RequestHandler):
    def get(self, doc_id, doc_rev=None):
        doc_id = int(doc_id)

        doc = self.application.get_document_backend(doc_id)

        if doc_rev is None:
            doc_rev, _ = doc.get_latest()
        else:
            doc_rev = int(doc_rev)

        rev, w_ops, content = doc.get_history_operations_to_latest(doc_rev)

        if doc_rev > rev:
            self.set_status(404)
            return self.finish({
                "error": "revision not found"
            })

        name, ts, _ = w_ops[0]

        for _, _, op in reversed(w_ops[1:]):
            content = op(content)

        self.finish({
            "rev": doc_rev,
            "author_name": name,
            "ts": ts,
            "content": content
        })


class RESTRouter(object):
    def __init__(self, prefix):
        self.prefix = prefix

    @property
    def urls(self):
        return [
            (self.prefix + r"/docs/(?P<doc_id>\d+)/?", DocumentMetaHandler),
            (self.prefix + r"/docs/(?P<doc_id>\d+)/revs/(?P<doc_rev>\d+)/?", DocumentRevisionHandler),
            (self.prefix + r"/docs/(?P<doc_id>\d+)/revs/latest/?", DocumentRevisionHandler)
        ]
