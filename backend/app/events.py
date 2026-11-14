"""Session-Ereignisse: Preishistorie Material (und später Änderungsprotokoll)."""
from datetime import date

from sqlalchemy import event, inspect
from sqlalchemy.orm import Session

from .context import current_user_id
from .models import Material, MaterialPrice


@event.listens_for(Session, "before_flush")
def material_price_history(session, flush_context, instances):
    for obj in list(session.new) + list(session.dirty):
        if not isinstance(obj, Material):
            continue
        hist = inspect(obj).attrs.price_per_kg.history
        if obj in session.new or hist.has_changes():
            obj.price_valid_from = obj.price_valid_from if (obj in session.new and obj.price_valid_from) else date.today()
            session.add(MaterialPrice(material=obj, price_per_kg=obj.price_per_kg, valid_from=obj.price_valid_from,
                                      user_id=current_user_id.get(), note="Anlage" if obj in session.new else "Preisänderung"))
