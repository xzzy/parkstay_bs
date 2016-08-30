from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.urlresolvers import reverse_lazy, reverse
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic.base import View, TemplateView
from django.views.generic.edit import FormView

from preserialize.serialize import serialize

from ledger.accounts.models import Profile, Document, EmailUser
from ledger.accounts.forms import AddressForm, ProfileForm, EmailUserForm, DocumentForm

from wildlifelicensing.apps.main.models import CommunicationsLogEntry,\
    WildlifeLicence
from wildlifelicensing.apps.main.forms import IdentificationForm, CommunicationsLogEntryForm
from wildlifelicensing.apps.main.mixins import CustomerRequiredMixin, OfficerRequiredMixin
from wildlifelicensing.apps.main.signals import identification_uploaded
from wildlifelicensing.apps.main.serializers import WildlifeLicensingJSONEncoder
from wildlifelicensing.apps.main.utils import format_communications_log_entry
from wildlifelicensing.apps.main.pdf import create_licence_renewal_pdf_bytes, bulk_licence_renewal_pdf_bytes


class SearchCustomersView(OfficerRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        query = request.GET.get('q')

        if query is not None:
            q = Q(first_name__icontains=query) | Q(last_name__icontains=query) & Q(groups=None)
            qs = EmailUser.objects.filter(q)
        else:
            qs = EmailUser.objects.none()

        users = [{'id': email_user.id, 'text': email_user.get_full_name_dob()} for email_user in qs]

        return JsonResponse(users, safe=False, encoder=WildlifeLicensingJSONEncoder)


class ListProfilesView(CustomerRequiredMixin, TemplateView):
    template_name = 'wl/list_profiles.html'
    login_url = '/'

    def get_context_data(self, **kwargs):
        context = super(ListProfilesView, self).get_context_data(**kwargs)

        def posthook(instance, attr):
            attr["auth_identity"] = instance.auth_identity
            return attr

        context['data'] = serialize(Profile.objects.filter(user=self.request.user))

        return context


class CreateProfilesView(CustomerRequiredMixin, TemplateView):
    template_name = 'wl/create_profile.html'
    login_url = '/'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {'profile_form': ProfileForm(user=request.user),
                                                    'address_form': AddressForm()})

    def post(self, request, *args, **kwargs):
        if request.user.pk != int(request.POST['user']):
            return HttpResponse('Unauthorized', status=401)

        profile_form = ProfileForm(request.POST)
        address_form = AddressForm(request.POST)

        if profile_form.is_valid() and address_form.is_valid():
            profile = profile_form.save(commit=False)
            profile.postal_address = address_form.save()
            profile.save()
        else:
            return render(request, self.template_name, {'profile_form': profile_form,
                                                        'address_form': address_form})

        messages.success(request, "The profile '%s' was created." % profile.name)

        return redirect('wl_main:list_profiles')


class DeleteProfileView(CustomerRequiredMixin, TemplateView):
    template_name = 'wl/list_profiles.html'
    login_url = '/'

    def get(self, request, id, *args, **kwargs):
        profile = get_object_or_404(Profile, pk=id)
        profile.delete()
        messages.success(request, "The profile '%s' was deleted." % profile.name)
        return redirect('wl_main:list_profiles')


class EditProfilesView(CustomerRequiredMixin, TemplateView):
    template_name = 'wl/edit_profile.html'
    login_url = '/'

    def get(self, request, *args, **kwargs):
        profile = get_object_or_404(Profile, pk=args[0])

        if profile.user != request.user:
            return HttpResponse('Unauthorized', status=401)

        return render(request, self.template_name, {'profile_form': ProfileForm(instance=profile),
                                                    'address_form': AddressForm(instance=profile.postal_address)})

    def post(self, request, *args, **kwargs):
        profile = get_object_or_404(Profile, pk=args[0])

        if profile.user != request.user or request.user.pk != int(request.POST['user']):
            return HttpResponse('Unauthorized', status=401)
        profile_form = ProfileForm(request.POST, instance=profile)
        address_form = AddressForm(request.POST, instance=profile.postal_address)

        if profile_form.is_valid() and address_form.is_valid():
            profile = profile_form.save()
            address_form.save()
        else:
            return render(request, self.template_name, {'profile_form': profile_form,
                                                        'address_form': address_form})

        messages.success(request, "The profile '%s' was updated." % profile.name)

        return redirect('wl_main:list_profiles')


class IdentificationView(LoginRequiredMixin, FormView):
    template_name = 'wl/manage_identification.html'
    login_url = '/'
    form_class = IdentificationForm
    success_url = reverse_lazy('wl_main:identification')

    def form_valid(self, form):
        if self.request.user.identification is not None:
            self.request.user.identification.delete()

        self.request.user.identification = Document.objects.create(file=self.request.FILES['identification_file'])
        self.request.user.save()

        identification_uploaded.send(sender=self.__class__, user=self.request.user)

        return super(IdentificationView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        kwargs['file_types'] = ', '.join(['.' + file_ext for file_ext in IdentificationForm.VALID_FILE_TYPES])

        if self.request.user.identification is not None:
            kwargs['existing_id_image_url'] = self.request.user.identification.file.url

        return super(IdentificationView, self).get_context_data(**kwargs)


class EditAccountView(CustomerRequiredMixin, TemplateView):
    template_name = 'wl/edit_account.html'
    login_url = '/'
    identification_url = reverse_lazy('wl_main:identification')

    def get(self, request, *args, **kwargs):
        emailuser = get_object_or_404(EmailUser, pk=request.user.id)
        # if user doesn't choose a identification, display a warning message
        if not emailuser.identification:
            messages.warning(request, "Please upload your identification.")

        return render(request, self.template_name, {'emailuser_form': EmailUserForm(instance=emailuser),})

    def post(self, request, *args, **kwargs):
        emailuser = get_object_or_404(EmailUser, pk=request.user.pk)
        # Save the original user data.
        original_first_name = emailuser.first_name
        original_last_name = emailuser.last_name
        emailuser_form = EmailUserForm(request.POST, instance=emailuser)
        if emailuser_form.is_valid():
            emailuser = emailuser_form.save(commit=False)
            is_name_changed = any([original_first_name != emailuser.first_name, original_last_name != emailuser.last_name])

            # send signal if either first name or last name is changed
            if is_name_changed:
                messages.warning(request, "Please upload new identification after you changed your name.")
                return redirect(self.identification_url)
            elif not emailuser.identification:
                messages.warning(request, "Please upload your identification.")
            else:
                messages.success(request, "User account was saved.")

        return render(request, self.template_name, {'emailuser_form': emailuser_form,})


class ListDocumentView(CustomerRequiredMixin, TemplateView):
    template_name = 'wl/list_documents.html'
    login_url = '/'

    def get_context_data(self, **kwargs):
        context = super(ListDocumentView, self).get_context_data(**kwargs)

        context['data'] = serialize(self.request.user.documents.all())

        return context


class LicenceRenewalPDFView(OfficerRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        licence = get_object_or_404(WildlifeLicence, pk=self.args[0])

        filename = '{}-{}-renewal.pdf'.format(licence.licence_number, licence.licence_sequence)

        response = HttpResponse(content_type='application/pdf')

        response.write(create_licence_renewal_pdf_bytes(filename, licence,
                                                        request.build_absolute_uri(reverse('home'))))

        return response


class BulkLicenceRenewalPDFView(OfficerRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        query = request.POST.get('query')
        licences = []
        if query:
            licences = WildlifeLicence.objects.filter(query)
        filename = 'bulk-renewals.pdf'
        response = HttpResponse(content_type='application/pdf')
        response.write(bulk_licence_renewal_pdf_bytes(licences, request.build_absolute_uri(reverse('home'))))
        return response


class CommunicationsLogListView(OfficerRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        q = Q(officer=args[0]) | Q(customer=args[0])

        data = serialize(CommunicationsLogEntry.objects.filter(q).order_by('created'),
                         posthook=format_communications_log_entry,
                         exclude=['communicationslogentry_ptr', 'customer', 'officer']),

        return JsonResponse({'data': data[0]}, safe=False, encoder=WildlifeLicensingJSONEncoder)


class AddCommunicationsLogEntryView(OfficerRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        customer = get_object_or_404(EmailUser, pk=args[0])

        form = CommunicationsLogEntryForm(data=request.POST, files=request.FILES)

        if form.is_valid():
            communications_log_entry = form.save(commit=False)

            communications_log_entry.customer = customer
            communications_log_entry.officer = request.user
            communications_log_entry.save()
            if request.FILES and 'attachment' in request.FILES:
                communications_log_entry.documents.add(Document.objects.create(file=request.FILES['attachment']))

            return JsonResponse('ok', safe=False, encoder=WildlifeLicensingJSONEncoder)
        else:
            return JsonResponse(
                {
                    "errors": [
                        {
                            'status': "422",
                            'title': 'Data not valid',
                            'detail': form.errors
                        }
                    ]
                },
                safe=False, encoder=WildlifeLicensingJSONEncoder, status_code=422)
