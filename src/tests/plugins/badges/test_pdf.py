from datetime import timedelta
from decimal import Decimal
from io import BytesIO

import pytest
from django.utils.timezone import now
from PyPDF2 import PdfFileReader

from pretix.base.models import (
    Event, Item, ItemVariation, Order, OrderPosition, Organizer,
)
from pretix.plugins.badges.exporters import BadgeExporter


@pytest.fixture
def env():
    o = Organizer.objects.create(name='Dummy', slug='dummy')
    event = Event.objects.create(
        organizer=o, name='Dummy', slug='dummy',
        date_from=now(), live=True
    )
    o1 = Order.objects.create(
        code='FOOBAR', event=event, email='dummy@dummy.test',
        status=Order.STATUS_PENDING,
        datetime=now(), expires=now() + timedelta(days=10),
        total=Decimal('13.37'), payment_provider='banktransfer'
    )
    shirt = Item.objects.create(event=event, name='T-Shirt', default_price=12)
    shirt_red = ItemVariation.objects.create(item=shirt, default_price=14, value="Red")
    OrderPosition.objects.create(
        order=o1, item=shirt, variation=shirt_red,
        price=12, attendee_name=None, secret='1234'
    )
    OrderPosition.objects.create(
        order=o1, item=shirt, variation=shirt_red,
        price=12, attendee_name=None, secret='5678'
    )
    return event, o1, shirt


@pytest.mark.django_db
def test_generate_pdf(env):
    event, order, shirt = env
    event.badge_layouts.create(name="Default", default=True)
    e = BadgeExporter(event)
    fname, ftype, buf = e.render({
        'items': [shirt.pk],
        'include_pending': False
    })
    assert ftype == 'application/pdf'
    pdf = PdfFileReader(BytesIO(buf))
    assert pdf.numPages == 0

    fname, ftype, buf = e.render({
        'items': [],
        'include_pending': True
    })
    assert ftype == 'application/pdf'
    pdf = PdfFileReader(BytesIO(buf))
    assert pdf.numPages == 0

    fname, ftype, buf = e.render({
        'items': [shirt.pk],
        'include_pending': True
    })
    assert ftype == 'application/pdf'
    pdf = PdfFileReader(BytesIO(buf))
    assert pdf.numPages == 2