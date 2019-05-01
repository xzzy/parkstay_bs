from django.http import HttpResponse,JsonResponse
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View, TemplateView
from commercialoperator.components.proposals.utils import create_data_from_form
from commercialoperator.components.proposals.models import Proposal, Referral, ProposalType, HelpPage
from commercialoperator.components.approvals.models import Approval
from commercialoperator.components.compliances.models import Compliance
import json,traceback
from reversion_compare.views import HistoryCompareDetailView
from reversion.models import Version

class ProposalView(TemplateView):
    template_name = 'commercialoperator/proposal.html'

    def post(self, request, *args, **kwargs):
        extracted_fields = []
        #import ipdb; ipdb.set_trace()
        try:
            proposal_id = request.POST.pop('proposal_id')
            proposal = Proposal.objects.get(proposal_id)
            schema = json.loads(request.POST.pop('schema')[0])
            extracted_fields = create_data_from_form(schema,request.POST, request.FILES)
            proposal.schema = schema;
            proposal.data = extracted_fields
            proposal.save()
            return redirect(reverse('external'))
        except:
            traceback.print_exc
            return JsonResponse({error:"something went wrong"},safe=False,status=400)


class ProposalHistoryCompareView(HistoryCompareDetailView):
    """
    View for reversion_compare
    """
    model = Proposal
    template_name = 'commercialoperator/reversion_history.html'


class ProposalFilteredHistoryCompareView(HistoryCompareDetailView):
    """
    View for reversion_compare - with 'status' in the comment field only'
    """
    model = Proposal
    template_name = 'commercialoperator/reversion_history.html'

    def _get_action_list(self,):
        action_list = [
            {"version": version, "revision": version.revision}
            for version in self._order_version_queryset(
                Version.objects.get_for_object(self.get_object()).select_related("revision__user").filter(revision__comment__icontains='status')
            )
        ]
        return action_list


class ReferralHistoryCompareView(HistoryCompareDetailView):
    """
    View for reversion_compare
    """
    model = Referral
    template_name = 'commercialoperator/reversion_history.html'


class ApprovalHistoryCompareView(HistoryCompareDetailView):
    """
    View for reversion_compare
    """
    model = Approval
    template_name = 'commercialoperator/reversion_history.html'


class ComplianceHistoryCompareView(HistoryCompareDetailView):
    """
    View for reversion_compare
    """
    model = Compliance
    template_name = 'commercialoperator/reversion_history.html'



class ProposalTypeHistoryCompareView(HistoryCompareDetailView):
    """
    View for reversion_compare
    """
    model = ProposalType
    template_name = 'commercialoperator/reversion_history.html'


class HelpPageHistoryCompareView(HistoryCompareDetailView):
    """
    View for reversion_compare
    """
    model = HelpPage
    template_name = 'commercialoperator/reversion_history.html'


