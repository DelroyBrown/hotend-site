from datetime import datetime
from random import randint

from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.generics import RetrieveAPIView, CreateAPIView, UpdateAPIView, get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from base_models.base_view_classes.api import GetOrCreateView, SearchView
from ..models import Machine, Operator, Sku, UniqueID, WorkOrder, ZeroingLog, MachineUsage


class CreateNewV6Barcode(APIView):
    iteration_limit = 200

    def get(self, request, *args, **kwargs):
        for i in range(self.iteration_limit):
            # Generate a random 9-digit number in string form, left-padded with zeros.
            code_value = randint(0, 999999999)
            code = str(code_value).zfill(9)

            # Check if this barcode has already been used.
            # Iterate again if so.
            if UniqueID.objects.filter(code=code).exists():
                continue

            # Otherwise, save a new empty UniqueID object to store the new barcode, and
            # send the barcode to the user.
            UniqueID.objects.create(code=code)

            return Response({"barcode": code})

        # If the loop ends, send the user a timeout error. They're welcome to try again,
        # but this helps avoid infinite loops due to bugs or the barcode selection filling up.
        msg = "Tried {} barcodes and couldn't find any unique ones!".format(self.iteration_limit)
        return Response({"error": msg}, status=500)


class GetOrCreateUniqueID(GetOrCreateView):
    model = UniqueID
    identity_fields = ["code"]


class GetOperator(RetrieveAPIView):
    lookup_url_kwarg = "code"
    lookup_field = "code"
    queryset = Operator.objects.all()
    serializer_class = Operator.generate_serializer_class()


class GetSku(RetrieveAPIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    lookup_url_kwarg = "code"
    lookup_field = "code"
    queryset = Sku.objects.all()
    serializer_class = Sku.generate_serializer_class()


class GetMachineByHostname(RetrieveAPIView):
    lookup_url_kwarg = "hostname"
    queryset = Machine.objects.all()
    serializer_class = Machine.generate_serializer_class()


class GetOrCreateWorkOrder(GetOrCreateView):
    model = WorkOrder
    identity_fields = ["code"]


class CreateZeroingLog(CreateAPIView):
    queryset = ZeroingLog.objects.all()
    serializer_class = ZeroingLog.generate_serializer_class()


class SearchSku(SearchView):
    """
    Searches for SKUs based on search terms in the URL. Each search term (separated by spaces) must be found
    somewhere in the SKU's code for a correct match.

    All matches are case-insensitive (using Django's __icontains).
    """
    queryset = Sku.objects.all()
    serializer_class = Sku.generate_serializer_class()
    authentication_classes = [SessionAuthentication]

    max_results = 30
    search_fields = ["code"]
    order_results_by = ["code"]


class SearchOperator(SearchView):
    queryset = Operator.objects.all()
    serializer_class = Operator.generate_serializer_class()
    authentication_classes = [SessionAuthentication]

    max_results = 30
    search_fields = ["code", "name"]
    order_results_by = ["name"]


class SearchMachine(SearchView):
    queryset = Machine.objects.all()
    serializer_class = Machine.generate_serializer_class()
    authentication_classes = [SessionAuthentication]

    max_results = 30
    search_fields = ["hostname", "name", "production_step"]
    order_results_by = ["name"]


class MachinePing(APIView):
    def post(self, request, *args, **kwargs):
        hostname = request.data.get('hostname', None)
        operator_id = request.data.get('operator_id', None)
        logging_out = request.data.get('logging_out', False)

        if operator_id is None:
            logging_out = True

        msg = f"Could not find machine {hostname}"
        if hostname is None:
            return Response({"error": msg}, status=500)
        machine = Machine.objects.filter(hostname=hostname).first()
        if machine is None:
            return Response({"error": msg}, status=500)

        last_login = MachineUsage.objects.filter(machine=machine).first()

        # edge case log out if operator not provided
        if logging_out:
            if last_login is not None and last_login.logged_out_at is None:
                return Response(last_login.log_out().to_dict())
            return Response({"error": "Machine not logged in"}, status=400)

        msg = f"Could not find machine {operator_id}"
        if operator_id is None:
            return Response({"error": msg}, status=500)
        operator = Operator.objects.filter(code=operator_id).first()
        if operator is None:
            return Response({"error": msg}, status=500)

        # if no last_login
        if last_login is None:
            return Response(MachineUsage.log_in(machine, operator).to_dict())

        # ping machine
        return Response(last_login.ping(operator, logging_out).to_dict())
