# models.py (ACTUALIZACIONES)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Boolean, Integer, Float, Text, Date, Time, DateTime, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, time
from enum import Enum
from typing import List, Optional
import secrets

db = SQLAlchemy()

# ============= ENUMS =============


class UserRole(Enum):
    USER = "user"
    ADMIN = "admin"


class BookingStatus(Enum):
    CART = "cart"
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class DayOfWeek(Enum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class ExtraType(Enum):
    PER_BOOKING = "per_booking"
    PER_GUEST = "per_guest"


class PaymentStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"


class EmailStatus(Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"

# ============= USUARIOS =============


class User(db.Model):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(
        String(120), unique=True, nullable=False, index=True)
    password: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True)  # Nullable para guest checkout
    is_active: Mapped[bool] = mapped_column(
        Boolean(), default=True, nullable=False)

    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # NUEVO: Sistema de verificación de email
    email_verified: Mapped[bool] = mapped_column(
        Boolean(), default=False, nullable=False)
    verification_token: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, unique=True)
    verification_token_expires: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True)

    # NUEVO: Reset de contraseña
    password_reset_token: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, unique=True)
    password_reset_expires: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True)

    # NUEVO: Para guest checkout (usuarios sin cuenta)
    is_guest: Mapped[bool] = mapped_column(
        Boolean(), default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow)
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True)

    # Relaciones
    bookings: Mapped[List["Booking"]] = relationship(
        back_populates='user', lazy='dynamic')

    def serialize(self):
        return {
            "id": self.id,
            "email": self.email,
            "is_active": self.is_active,
            "role": self.role.value,
            "name": self.name,
            "phone": self.phone,
            "email_verified": self.email_verified,
            "is_guest": self.is_guest,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None
        }

    def is_admin(self):
        return self.role == UserRole.ADMIN

    def generate_verification_token(self):
        """Generar token de verificación de email"""
        self.verification_token = secrets.token_urlsafe(32)
        self.verification_token_expires = datetime.utcnow() + timedelta(hours=24)
        return self.verification_token

    def generate_password_reset_token(self):
        """Generar token de reset de contraseña"""
        self.password_reset_token = secrets.token_urlsafe(32)
        self.password_reset_expires = datetime.utcnow() + timedelta(hours=2)
        return self.password_reset_token

# ============= EXPERIENCIAS (sin cambios) =============


class Experience(db.Model):
    __tablename__ = 'experiences'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    max_capacity: Mapped[int] = mapped_column(
        Integer, default=20, nullable=False)
    duration_hours: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean(), default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow)

    schedules: Mapped[List["ExperienceSchedule"]] = relationship(
        back_populates='experience', cascade='all, delete-orphan')
    bookings: Mapped[List["Booking"]] = relationship(
        back_populates='experience')

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'max_capacity': self.max_capacity,
            'duration_hours': self.duration_hours,
            'image_url': self.image_url,
            'is_active': self.is_active,
            'schedules': [schedule.serialize() for schedule in self.schedules]
        }


class ExperienceSchedule(db.Model):
    __tablename__ = 'experience_schedules'

    id: Mapped[int] = mapped_column(primary_key=True)
    experience_id: Mapped[int] = mapped_column(
        Integer, db.ForeignKey('experiences.id'), nullable=False)
    day_of_week: Mapped[DayOfWeek] = mapped_column(
        SQLEnum(DayOfWeek), nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)

    experience: Mapped["Experience"] = relationship(back_populates='schedules')

    def serialize(self):
        return {
            'id': self.id,
            'day_of_week': self.day_of_week.value,
            'start_time': self.start_time.strftime('%H:%M') if self.start_time else None
        }

# ============= HABITACIONES (sin cambios) =============


class Room(db.Model):
    __tablename__ = 'rooms'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    price_per_night: Mapped[float] = mapped_column(Float, nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True)
    amenities: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean(), default=True)
    check_in_time: Mapped[time] = mapped_column(
        Time, default=time(15, 0), nullable=False)
    check_out_time: Mapped[time] = mapped_column(
        Time, default=time(11, 0), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow)

    booking_rooms: Mapped[List["BookingRoom"]
                          ] = relationship(back_populates='room')

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'capacity': self.capacity,
            'price_per_night': self.price_per_night,
            'image_url': self.image_url,
            'amenities': self.amenities,
            'is_active': self.is_active,
            'check_in_time': self.check_in_time.strftime('%H:%M'),
            'check_out_time': self.check_out_time.strftime('%H:%M')
        }

# ============= EXTRAS (sin cambios) =============


class Extra(db.Model):
    __tablename__ = 'extras'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    type: Mapped[ExtraType] = mapped_column(SQLEnum(ExtraType), nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean(), default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow)

    booking_extras: Mapped[List["BookingExtra"]
                           ] = relationship(back_populates='extra')

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'type': self.type.value,
            'image_url': self.image_url,
            'is_active': self.is_active
        }

# ============= PAQUETES (sin cambios) =============


class Package(db.Model):
    __tablename__ = 'packages'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean(), default=True)
    room_id: Mapped[Optional[int]] = mapped_column(
        Integer, db.ForeignKey('rooms.id'), nullable=True)
    experience_id: Mapped[Optional[int]] = mapped_column(
        Integer, db.ForeignKey('experiences.id'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow)

    room: Mapped[Optional["Room"]] = relationship()
    experience: Mapped[Optional["Experience"]] = relationship()
    included_extras: Mapped[List["PackageExtra"]] = relationship(
        back_populates='package', cascade='all, delete-orphan')
    bookings: Mapped[List["Booking"]] = relationship(back_populates='package')

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'image_url': self.image_url,
            'room': self.room.serialize() if self.room else None,
            'experience': self.experience.serialize() if self.experience else None,
            'included_extras': [pe.serialize() for pe in self.included_extras],
            'is_active': self.is_active
        }


class PackageExtra(db.Model):
    __tablename__ = 'package_extras'

    id: Mapped[int] = mapped_column(primary_key=True)
    package_id: Mapped[int] = mapped_column(
        Integer, db.ForeignKey('packages.id'), nullable=False)
    extra_id: Mapped[int] = mapped_column(
        Integer, db.ForeignKey('extras.id'), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1)

    package: Mapped["Package"] = relationship(back_populates='included_extras')
    extra: Mapped["Extra"] = relationship()

    def serialize(self):
        return {
            'id': self.id,
            'extra': self.extra.serialize(),
            'quantity': self.quantity
        }

# ============= RESERVAS =============


class Booking(db.Model):
    __tablename__ = 'bookings'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, db.ForeignKey('users.id'), nullable=False)

    # NUEVO: Número de confirmación único
    confirmation_number: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True)

    experience_id: Mapped[Optional[int]] = mapped_column(
        Integer, db.ForeignKey('experiences.id'), nullable=True)
    package_id: Mapped[Optional[int]] = mapped_column(
        Integer, db.ForeignKey('packages.id'), nullable=True)

    experience_date: Mapped[Optional[datetime]
                            ] = mapped_column(Date, nullable=True)
    experience_time: Mapped[Optional[time]
                            ] = mapped_column(Time, nullable=True)

    check_in: Mapped[Optional[datetime]] = mapped_column(Date, nullable=True)
    check_out: Mapped[Optional[datetime]] = mapped_column(Date, nullable=True)
    check_in_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    check_out_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)

    number_of_guests: Mapped[int] = mapped_column(Integer, nullable=False)

    status: Mapped[BookingStatus] = mapped_column(
        SQLEnum(BookingStatus), default=BookingStatus.CART)
    total_price: Mapped[float] = mapped_column(Float, nullable=False)

    stripe_payment_intent_id: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True)
    stripe_payment_status: Mapped[Optional[str]
                                  ] = mapped_column(String(50), nullable=True)
    payment_status: Mapped[PaymentStatus] = mapped_column(
        SQLEnum(PaymentStatus), default=PaymentStatus.PENDING)

    special_requests: Mapped[Optional[str]
                             ] = mapped_column(Text, nullable=True)
    admin_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    cart_expires_at: Mapped[Optional[datetime]
                            ] = mapped_column(DateTime, nullable=True)

    # Relaciones
    user: Mapped["User"] = relationship(back_populates='bookings')
    experience: Mapped[Optional["Experience"]
                       ] = relationship(back_populates='bookings')
    package: Mapped[Optional["Package"]] = relationship(
        back_populates='bookings')
    rooms: Mapped[List["BookingRoom"]] = relationship(
        back_populates='booking', cascade='all, delete-orphan')
    extras: Mapped[List["BookingExtra"]] = relationship(
        back_populates='booking', cascade='all, delete-orphan')
    email_logs: Mapped[List["EmailLog"]] = relationship(
        back_populates='booking', cascade='all, delete-orphan')

    def serialize(self):
        return {
            'id': self.id,
            'confirmation_number': self.confirmation_number,
            'user': self.user.serialize(),
            'experience': self.experience.serialize() if self.experience else None,
            'package': self.package.serialize() if self.package else None,
            'experience_date': self.experience_date.isoformat() if self.experience_date else None,
            'experience_time': self.experience_time.strftime('%H:%M') if self.experience_time else None,
            'check_in': self.check_in.isoformat() if self.check_in else None,
            'check_out': self.check_out.isoformat() if self.check_out else None,
            'check_in_time': self.check_in_time.strftime('%H:%M') if self.check_in_time else None,
            'check_out_time': self.check_out_time.strftime('%H:%M') if self.check_out_time else None,
            'number_of_guests': self.number_of_guests,
            'status': self.status.value,
            'payment_status': self.payment_status.value,
            'total_price': self.total_price,
            'rooms': [br.serialize() for br in self.rooms],
            'extras': [be.serialize() for be in self.extras],
            'special_requests': self.special_requests,
            'admin_notes': self.admin_notes,
            'stripe_payment_intent_id': self.stripe_payment_intent_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'cart_expires_at': self.cart_expires_at.isoformat() if self.cart_expires_at else None
        }

    def serialize_admin(self):
        data = self.serialize()
        data['stripe_details'] = {
            'payment_intent_id': self.stripe_payment_intent_id,
            'payment_status': self.stripe_payment_status,
            'payment_status_enum': self.payment_status.value
        }
        return data

    @staticmethod
    def generate_confirmation_number():
        """Generar número de confirmación único (ej: BK20240115ABCD)"""
        import random
        import string
        date_str = datetime.utcnow().strftime('%Y%m%d')
        random_str = ''.join(random.choices(
            string.ascii_uppercase + string.digits, k=4))
        return f"BK{date_str}{random_str}"


class BookingRoom(db.Model):
    __tablename__ = 'booking_rooms'

    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[int] = mapped_column(
        Integer, db.ForeignKey('bookings.id'), nullable=False)
    room_id: Mapped[int] = mapped_column(
        Integer, db.ForeignKey('rooms.id'), nullable=False)
    check_in: Mapped[datetime] = mapped_column(Date, nullable=False)
    check_out: Mapped[datetime] = mapped_column(Date, nullable=False)
    nights: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)

    booking: Mapped["Booking"] = relationship(back_populates='rooms')
    room: Mapped["Room"] = relationship(back_populates='booking_rooms')

    def serialize(self):
        return {
            'id': self.id,
            'room': self.room.serialize(),
            'check_in': self.check_in.isoformat(),
            'check_out': self.check_out.isoformat(),
            'nights': self.nights,
            'price': self.price
        }


class BookingExtra(db.Model):
    __tablename__ = 'booking_extras'

    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[int] = mapped_column(
        Integer, db.ForeignKey('bookings.id'), nullable=False)
    extra_id: Mapped[int] = mapped_column(
        Integer, db.ForeignKey('extras.id'), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    price: Mapped[float] = mapped_column(Float, nullable=False)

    booking: Mapped["Booking"] = relationship(back_populates='extras')
    extra: Mapped["Extra"] = relationship(back_populates='booking_extras')

    def serialize(self):
        return {
            'id': self.id,
            'extra': self.extra.serialize(),
            'quantity': self.quantity,
            'price': self.price
        }

# ============= EMAIL LOG =============


class EmailLog(db.Model):
    __tablename__ = 'email_logs'

    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[int] = mapped_column(
        Integer, db.ForeignKey('bookings.id'), nullable=False)
    # 'booking_confirmation', 'payment_receipt', etc.
    email_type: Mapped[str] = mapped_column(String(50), nullable=False)
    recipient_email: Mapped[str] = mapped_column(String(120), nullable=False)
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[EmailStatus] = mapped_column(
        SQLEnum(EmailStatus), default=EmailStatus.PENDING)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow)

    booking: Mapped["Booking"] = relationship(back_populates='email_logs')

    def serialize(self):
        return {
            'id': self.id,
            'booking_id': self.booking_id,
            'email_type': self.email_type,
            'recipient_email': self.recipient_email,
            'subject': self.subject,
            'status': self.status.value,
            'error_message': self.error_message,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'created_at': self.created_at.isoformat()
        }

# ============= DISPONIBILIDAD (sin cambios) =============


class RoomAvailability(db.Model):
    __tablename__ = 'room_availability'

    id: Mapped[int] = mapped_column(primary_key=True)
    room_id: Mapped[int] = mapped_column(
        Integer, db.ForeignKey('rooms.id'), nullable=False)
    date: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)
    is_available: Mapped[bool] = mapped_column(Boolean(), default=True)
    reason: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    room: Mapped["Room"] = relationship()

    __table_args__ = (
        db.UniqueConstraint('room_id', 'date', name='_room_date_uc'),
    )

    def serialize(self):
        return {
            'id': self.id,
            'room_id': self.room_id,
            'date': self.date.isoformat(),
            'is_available': self.is_available,
            'reason': self.reason
        }


class ExperienceAvailability(db.Model):
    __tablename__ = 'experience_availability'

    id: Mapped[int] = mapped_column(primary_key=True)
    experience_id: Mapped[int] = mapped_column(
        Integer, db.ForeignKey('experiences.id'), nullable=False)
    date: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)
    available_spots: Mapped[int] = mapped_column(Integer, nullable=False)

    experience: Mapped["Experience"] = relationship()

    __table_args__ = (
        db.UniqueConstraint('experience_id', 'date', name='_experience_date_uc'),
    )

    def serialize(self):
        return {
            'id': self.id,
            'experience_id': self.experience_id,
            'date': self.date.isoformat(),
            'available_spots': self.available_spots
        }


class BookingItem(db.Model):
    __tablename__ = 'booking_items'

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)

    item_type = db.Column(db.String(50), nullable=False)  # 'experience' o 'room'

    experience_id = db.Column(db.Integer, db.ForeignKey('experiences.id'), nullable=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=True)

    name = db.Column(db.String(200), nullable=False)
    image_url = db.Column(db.String(500))

    date = db.Column(db.Date, nullable=True)
    guests = db.Column(db.Integer)

    check_in = db.Column(db.Date, nullable=True)
    check_out = db.Column(db.Date, nullable=True)
    nights = db.Column(db.Integer)

    unit_price = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)

    extras = db.Column(db.JSON)  # [{id, name, price}, ...]

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    experience = db.relationship('Experience', backref='booking_items')
    room = db.relationship('Room', backref='booking_items')

    def serialize(self):
        return {
            'id': self.id,
            'type': self.item_type,
            'name': self.name,
            'image_url': self.image_url,
            'date': self.date.isoformat() if self.date else None,
            'check_in': self.check_in.isoformat() if self.check_in else None,
            'check_out': self.check_out.isoformat() if self.check_out else None,
            'guests': self.guests,
            'nights': self.nights,
            'unit_price': self.unit_price,
            'subtotal': self.subtotal,
            'extras': self.extras,
            'experience_id': self.experience_id,
            'room_id': self.room_id
        }
