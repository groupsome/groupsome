from django.shortcuts import render, get_object_or_404, redirect
from accounts.views import LoginRequiredMixin
from django.views.generic import View
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django.contrib import messages
from groups.views import get_group, prepare_context, require_role
from home.models import File, Directory
from events.views import get_telegram_user_from_request


class DirectoryView(LoginRequiredMixin, View):
    def get(self, request, group_id, directory_id=None):
        group = get_group(group_id, request.user)
        t_user = get_telegram_user_from_request(request)

        if directory_id is None:
            directory = None
        else:
            directory = get_object_or_404(Directory, id=directory_id)
            if directory.group != group:
                raise Http404()

        directories = Directory.objects.filter(group=group, parent=directory)
        files = File.objects.filter(group=group, directory=directory)

        context = {
            "directory": directory,
            "files": files,
            "directories": directories,
        }

        return render(request, "files/group/directory.html", prepare_context(group, t_user, context))


class CreateDirectoryView(LoginRequiredMixin, View):
    def post(self, request, group_id):
        group = get_group(group_id, request.user)
        require_role(request.user, group, "admin")

        name = request.POST.get("name", "")
        parent = int("0" + request.POST.get("parent", 0))

        parent_dir = None

        if name == "":
            messages.error(request, _("Something went wrong"))
            return HttpResponseRedirect(reverse("groups:file_overview", kwargs={"group_id": group_id}))

        if parent:
            parent_dir = Directory.objects.get(id=parent)
            if parent_dir is None or parent_dir.group != group:
                messages.error(request, _("Something went wrong"))
                return HttpResponseRedirect(reverse("groups:file_overview", kwargs={"group_id": group_id}))

        directory = Directory.create_and_save(group, name, parent_dir)
        return HttpResponseRedirect(reverse("groups:file_directory", kwargs={"group_id": group_id,
                                                                             "directory_id": directory.id}))


class DeleteDirectoryView(LoginRequiredMixin, View):
    def post(self, request, group_id, directory_id):
        group = get_group(group_id, request.user)
        require_role(request.user, group, "admin")
        directory = get_object_or_404(Directory, id=directory_id)

        if directory is None or directory.group != group:
            return JsonResponse({}, status=404)

        directory.delete()
        return JsonResponse({'message': _('Directory deleted')})


class DeleteFileView(LoginRequiredMixin, View):
    def post(self, request, group_id, file_id):
        group = get_group(group_id, request.user)
        require_role(request.user, group, "admin")
        file = get_object_or_404(File, id=file_id)

        if file is None or file.group != group:
            return JsonResponse({}, status=404)

        file.delete()
        return JsonResponse({'message': _('File deleted')})


class MoveFileView(LoginRequiredMixin, View):
    def post(self, request, group_id, file_id):
        group = get_group(group_id, request.user)
        require_role(request.user, group, "admin")
        file = get_object_or_404(File, id=file_id)

        if file.group != group:
            return JsonResponse({}, status=404)

        directory_id = int("0" + request.POST.get("directory", 0))

        directory = None

        if directory_id:
            directory = Directory.objects.get(id=directory_id)
            if directory is None or directory.group != group:
                return JsonResponse({}, status=404)

        file.directory = directory
        file.save()
        return JsonResponse({'message': _('File moved')})


class MoveDirectoryView(LoginRequiredMixin, View):
    def post(self, request, group_id, directory_id):
        group = get_group(group_id, request.user)
        require_role(request.user, group, "admin")
        directory = get_object_or_404(Directory, id=directory_id)

        if directory.group != group:
            return JsonResponse({}, status=404)

        directory_id = int("0" + request.POST.get("directory", 0))

        target = None

        if directory_id:
            target = Directory.objects.get(id=directory_id)
            if target is None or target.group != group or target == directory:
                return JsonResponse({}, status=404)

        directory.parent = target
        directory.save()
        return JsonResponse({'message': _('Directory moved')})
