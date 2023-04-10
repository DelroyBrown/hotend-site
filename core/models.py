import datetime
from base_models.generate_serializer_mixin import GenerateSerializerMixin
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.forms import model_to_dict


from .production_steps import PRODUCTION_STEPS
from .uid_schemas import UID_SCHEMAS


def validate_work_order_code(code):
    prefix = code[:7]
    if prefix not in ["E3D-WO-", "E3D-PO-", "E3D-CR-"]:
        raise ValidationError(F"Work Order '{code}' does not start with 'E3D-WO-', 'E3D-PO-', or 'E3D-CR-'")


class WorkOrder(GenerateSerializerMixin, models.Model):
    code = models.CharField(max_length=255, primary_key=True, validators=[validate_work_order_code])

    date_created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    is_test_data = models.BooleanField(default=False)

    def __str__(self):
        return self.code


class Sku(GenerateSerializerMixin, models.Model):
    code = models.CharField(max_length=255, primary_key=True)

    description = models.TextField(blank=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return self.code


class UniqueID(GenerateSerializerMixin, models.Model):
    code = models.CharField(max_length=255, primary_key=True)
    date_created = models.DateField(default=datetime.date.today)

    matches_schemas = ArrayField(
        models.CharField(max_length=255, choices=UID_SCHEMAS.choices()),
        default=list,
    )

    def __str__(self):
        return self.code

    def update_schemas(self):
        """
        Ensure the UID's code matches at least one valid schema; raise a ValidationError if it doesn't.
        Store the matched schemas on the model.
        """
        schemas = UID_SCHEMAS.match_all(self.code)
        if not schemas:
            raise ValidationError(f"UID code {self.code} doesn't match any known schema!")

        self.matches_schemas = [s.name for s in schemas]

    def clean(self):
        """Ensure the model matches at least one valid schema."""
        self.update_schemas()
        super().clean()

    def save(self, *args, **kwargs):
        """
        Ensure the model's matches_schemas field is up to date when saving.
        Note that this means that save() can raise ValidationError.
        """
        self.update_schemas()
        super().save(*args, **kwargs)


class Machine(GenerateSerializerMixin, models.Model):
    hostname = models.CharField(max_length=255, primary_key=True)

    name = models.CharField(max_length=255, unique=True)
    auto_update = models.BooleanField(default=False)
    production_step = models.CharField(max_length=255, choices=PRODUCTION_STEPS.choices)
    idealised_cycle_time = models.PositiveIntegerField(default=3600)
    planned_production_time = models.PositiveIntegerField(default=28800)
    required_ping_interval = models.PositiveIntegerField(default=600)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return F"{self.name} ({self.hostname})"


class Operator(GenerateSerializerMixin, models.Model):
    code = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class ZeroingLog(GenerateSerializerMixin, models.Model):
    date = models.DateTimeField(default=datetime.datetime.now)
    resistance = models.FloatField()
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)
    operator = models.ForeignKey(Operator, on_delete=models.CASCADE)

    def __str__(self):
        return F"{self.machine} zeroed at {self.date}"


class MachineUsage(GenerateSerializerMixin, models.Model):
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)
    operator = models.ForeignKey(Operator, on_delete=models.CASCADE)
    logged_in_at = models.DateTimeField(default=datetime.datetime.today)
    logged_out_at = models.DateTimeField(null=True)
    last_ping = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-logged_in_at"]

    def __str__(self) -> str:
        logged_in_indicator = "*" if self.logged_out_at is None else ""
        return f"{logged_in_indicator}{self.machine.hostname} ({self.operator}) - {self.logged_in_at.date()} for {self.duration}"

    @property
    def duration(self):
        if self.logged_out_at is None:
            return datetime.datetime.today() - self.logged_in_at
        return self.logged_out_at - self.logged_in_at

    def to_dict(self, *, exclude_fields=None):
        results = model_to_dict(self, exclude=exclude_fields)
        results['last_ping'] = self.last_ping
        return results

    @classmethod
    def log_in(cls, machine, operator):
        if type(machine) == str:
            machine = Machine.objects.filter(hostname=machine).first()
        log_in = MachineUsage.objects.create(
            machine=machine,
            operator=operator,
        )
        return log_in

    def log_out(self):
        logout_time = min(
            datetime.datetime.today(),
            self.last_ping + datetime.timedelta(seconds=self.machine.required_ping_interval))

        self.logged_out_at = logout_time
        self.save()
        return self

    def ping(self, operator, logging_out=False):
        ping_time = datetime.datetime.today()

        # if event is already logged out, create a new login event
        if self.logged_out_at is not None:
            if logging_out is False:
                return MachineUsage.log_in(self.machine, operator)
            return self

        if logging_out is True:
            return self.log_out()

        if (ping_time - self.last_ping).total_seconds() < self.machine.required_ping_interval:
            if operator == self.operator:
                self.last_ping = ping_time
                self.save()
                return self

            self.log_out()
            return MachineUsage.log_in(self.machine, operator)

        self.log_out()
        return MachineUsage.log_in(self.machine, operator)

    @classmethod
    def get_logged_in_machines(cls):
        logins = cls.objects.filter(logged_out_at=None)
        machines = [login.machine for login in logins]
        return machines

    @classmethod
    def get_active_duration(cls, machine=None, date_from=None, date_to=None):
        full_filter = Q()
        if machine is not None:
            full_filter &= Q(machine=machine)
        if date_from is not None:
            full_filter &= Q(logged_in_at__gte=date_from)
        if date_to is not None:
            full_filter &= Q(logged_out_at__lte=(date_to + datetime.timedelta(days=1)))

        # ignore machines that are still logged in
        full_filter &= ~Q(logged_out_at=None)

        logins = cls.objects.filter(full_filter)
        duration = datetime.timedelta(0)
        for login in logins:
            duration += login.duration
        return duration
