from tastypie.test import ResourceTestCase


class UnionResourceTest(ResourceTestCase):
    fixtures = ['testdump.json']

    def test_get_list_unauthorzied(self):
        self.assertHttpUnauthorized(self.api_client.get('/api/v1/unions/', format='json'))
