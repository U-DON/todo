from django.contrib.auth import get_user_model

from tastypie.authentication import SessionAuthentication
from tastypie.authorization import Authorization, DjangoAuthorization
from tastypie.resources import ModelResource

class UserAuthorization(Authorization):
    def read_list(self, object_list, bundle):
        return object_list.filter(user=bundle.request.user)

    def read_detail(self, object_list, bundle):
        return bundle.obj.user == bundle.request.user

    def create_list(self, object_list, bundle):
        return object_list

    def create_detail(self, object_list, bundle):
        return bundle.obj.user == bundle.request.user

    def update_list(self, object_list, bundle):
        allowed = []
        for obj in object_list:
            if obj.user == bundle.request.user:
                allowed.append(obj)
        return allowed

    def update_detail(self, object_list, bundle):
        return bundle.obj.user == bundle.request.user

    def delete_list(self, object_list, bundle):
        return object_list.filter(user=bundle.request.user)

    def delete_detail(self, object_list, bundle):
        return bundle.obj.user == bundle.request.user

class UserResource(ModelResource):
    class Meta:
        queryset = get_user_model().objects.all()
        resource_name = 'user'
        fields = ['name', 'email']
        authentication = SessionAuthentication()
        authorization = UserAuthorization()
