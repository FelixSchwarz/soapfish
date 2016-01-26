from __future__ import absolute_import

import unittest
from collections import namedtuple
from datetime import datetime

from pythonic_testcase import *  # noqa

from soapfish.django_ import django_dispatcher
from soapfish.testutil import echo_service, framework

try:
    import django
except ImportError:
    django = None
else:
    from django.conf import settings
    settings.configure(
        ROOT_URLCONF=None,
        DEBUG=True,
        DEBUG_PROPAGATE_EXCEPTIONS=True,
        EMAIL_BACKEND='django.core.mail.backends.dummy.EmailBackend',
        LOGGING_CONFIG=None,
        USE_I18N=False,
        USE_TZ=True,
    )
    from django.conf.urls import url
    from django.test import Client

urlconf = namedtuple('urlconf', 'urlpatterns')


@unittest.skipIf(django is None, 'Django is not installed.')
class DjangoDispatchTest(framework.DispatchTestMixin, PythonicTestCase):

    def setUp(self):  # noqa
        self.service = echo_service()
        settings.ROOT_URLCONF = urlconf(urlpatterns=[url(r'^ws/$', django_dispatcher(self.service))])
        if hasattr(django, 'setup'):
            django.setup()
        self.client = Client()

    def _prepare_extras(self, headers):
        extras = {'HTTP_' + k.replace('-', '_').upper(): v for k, v in headers.items()}
        extras.update(content_type=headers['content-type'])
        return extras

    def test_can_retrieve_wsdl(self):
        response = self.client.get('/ws/', {'wsdl': None})
        assert_equals(200, response.status_code)
        assert_equals('text/xml', response['Content-Type'])
        assert_contains('<wsdl:definitions', response.content)

    def test_can_dispatch_simple_request(self):
        input_value = str(datetime.now())
        headers, body = self._soap_request(input_value)
        extras = self._prepare_extras(headers)
        response = self.client.post('/ws/', body, **extras)
        assert_equals(200, response.status_code)
        body = self._soap_response(response.content)
        assert_equals(input_value, body.value)