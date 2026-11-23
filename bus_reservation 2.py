"""
BUS RESERVATION MANAGEMENT SYSTEM (Console Application)
Uses only the Python standard library - runs anywhere with Python 3.6+.
"""

from datetime import datetime

TABLE_WIDTH = 62


# ============================================================
#  CUSTOM EXCEPTIONS
# ============================================================
class ReservationError(Exception):
    """Base class for all reservation errors."""


class BusNotFoundError(ReservationError):
    """Raised when a bus ID does not exist."""


class SeatNotAvailableError(ReservationError):
    """Raised when the requested seat is already booked or invalid."""


class BookingNotFoundError(ReservationError):
    """Raised when a booking ID does not exist."""


# ============================================================
#  MODEL CLASSES
# ============================================================
class Passenger:
    def __init__(self, name, age, phone):
        self.name = name
        self.age = age
        self.phone = phone

    def __str__(self):
        return f"{self.name} (Age {self.age}, Phone {self.phone or 'N/A'})"


class Bus:
    """Base class for a bus. Subclasses change the fare and seat layout."""

    bus_type = "Standard"
    fare_multiplier = 1.0

    def __init__(self, bus_id, route, departure, base_fare, total_seats):
        self._bus_id = bus_id
        self._route = route
        self._departure = departure          # string like "08:30"
        self._base_fare = base_fare
        self._total_seats = total_seats
        self._seats = {}                     # seat_no -> Booking (only if booked)

    # ---- read-only properties (encapsulation) ----
    @property
    def bus_id(self):
        return self._bus_id

    @property
    def route(self):
        return self._route

    @property
    def departure(self):
        return self._departure

    @property
    def total_seats(self):
        return self._total_seats

    @property
    def fare(self):
        return round(self._base_fare * self.fare_multiplier, 2)

    # ---- seat handling ----
    def is_valid_seat(self, seat_no):
        return 1 <= seat_no <= self._total_seats

    def is_seat_free(self, seat_no):
        return seat_no not in self._seats

    def book_seat(self, seat_no, booking):
        if not self.is_valid_seat(seat_no):
            raise SeatNotAvailableError(
                f"Seat {seat_no} does not exist. Choose 1 to {self._total_seats}.")
        if not self.is_seat_free(seat_no):
            raise SeatNotAvailableError(f"Seat {seat_no} is already booked.")
        self._seats[seat_no] = booking

    def release_seat(self, seat_no):
        self._seats.pop(seat_no, None)

    def free_seats(self):
        return [s for s in range(1, self._total_seats + 1) if s not in self._seats]

    def booked_count(self):
        return len(self._seats)

    def show_seat_map(self):
        print(f"\n  Seat map for Bus {self._bus_id} ('X' = booked, number = free)")
        row = []
        for seat in range(1, self._total_seats + 1):
            label = "X " if seat in self._seats else f"{seat:<2}"
            row.append(label)
            if seat % 4 == 0 or seat == self._total_seats:
                print("   " + "  ".join(row))
                row = []

    def __str__(self):
        return (f"{self._bus_id:<6}{self._route[:22]:<24}{self.bus_type:<12}"
                f"{self._departure:<8}Rs.{self.fare:<9.2f}"
                f"{len(self.free_seats()):>2}/{self._total_seats} free")


class AC_Bus(Bus):
    """AC bus: higher fare, fewer seats (inheritance and polymorphism)."""
    bus_type = "AC"
    fare_multiplier = 1.5


class SleeperBus(Bus):
    """Sleeper bus: higher fare, sleeper berths."""
    bus_type = "Sleeper"
    fare_multiplier = 1.8


class Booking:
    """A single reservation made by a passenger on a bus."""

    _counter = 500   # class variable shared by all bookings

    def __init__(self, bus, passenger, seat_no):
        Booking._counter += 1
        self.booking_id = Booking._counter
        self.bus = bus
        self.passenger = passenger
        self.seat_no = seat_no
        self.booked_on = datetime.now()
        self.is_cancelled = False

    @property
    def amount(self):
        return self.bus.fare

    def ticket(self):
        line = "-" * TABLE_WIDTH
        return "\n".join([
            line,
            "                    BUS TICKET",
            line,
            f"Booking ID : {self.booking_id}",
            f"Passenger  : {self.passenger.name}",
            f"Age / Phone: {self.passenger.age} / {self.passenger.phone or 'N/A'}",
            f"Bus ID     : {self.bus.bus_id} ({self.bus.bus_type})",
            f"Route      : {self.bus.route}",
            f"Departure  : {self.bus.departure}",
            f"Seat No    : {self.seat_no}",
            f"Fare Paid  : Rs.{self.amount:.2f}",
            f"Booked On  : {self.booked_on:%d-%m-%Y %H:%M}",
            line,
        ])


# ============================================================
#  BUSINESS LOGIC CLASS
# ============================================================
class ReservationSystem:
    """Manages buses and bookings. Holds all data in memory."""

    def __init__(self, company_name):
        self.company_name = company_name
        self._buses = {}          # bus_id -> Bus
        self._bookings = {}       # booking_id -> Booking

    # ---- bus management ----
    def add_bus(self, bus):
        if bus.bus_id in self._buses:
            raise ReservationError(f"Bus ID {bus.bus_id} already exists.")
        self._buses[bus.bus_id] = bus

    def get_bus(self, bus_id):
        try:
            return self._buses[bus_id]
        except KeyError:
            raise BusNotFoundError(f"No bus found with ID '{bus_id}'.")

    def all_buses(self):
        return list(self._buses.values())

    def search_buses(self, route_keyword):
        keyword = route_keyword.lower()
        return [b for b in self._buses.values() if keyword in b.route.lower()]

    # ---- booking ----
    def book_ticket(self, bus_id, passenger, seat_no):
        bus = self.get_bus(bus_id)
        booking = Booking(bus, passenger, seat_no)
        bus.book_seat(seat_no, booking)    # raises if seat is taken
        self._bookings[booking.booking_id] = booking
        return booking

    def cancel_booking(self, booking_id):
        booking = self._bookings.get(booking_id)
        if booking is None:
            raise BookingNotFoundError(f"No booking found with ID {booking_id}.")
        if booking.is_cancelled:
            raise ReservationError("This booking is already cancelled.")
        booking.bus.release_seat(booking.seat_no)
        booking.is_cancelled = True
        return booking

    def find_booking(self, booking_id):
        booking = self._bookings.get(booking_id)
        if booking is None:
            raise BookingNotFoundError(f"No booking found with ID {booking_id}.")
        return booking

    def active_bookings(self):
        return [b for b in self._bookings.values() if not b.is_cancelled]

    def total_revenue(self):
        return sum(b.amount for b in self.active_bookings())


# ============================================================
#  INPUT HELPER FUNCTIONS (validation)
# ============================================================
def ask_nonempty(prompt):
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("  ! This field cannot be empty.")


def ask_int(prompt, minimum=None):
    while True:
        try:
            value = int(input(prompt).strip())
        except ValueError:
            print("  ! Please enter a whole number.")
            continue
        if minimum is not None and value < minimum:
            print(f"  ! Value must be at least {minimum}.")
            continue
        return value


def ask_age(prompt):
    while True:
        age = ask_int(prompt, minimum=1)
        if age <= 120:
            return age
        print("  ! Please enter a realistic age (1 to 120).")


def ask_yes_no(prompt):
    return input(prompt + " (y/n): ").strip().lower() == "y"


# ============================================================
#  CONSOLE APPLICATION CLASS
# ============================================================
class ReservationApp:
    """Handles the menu and user interaction."""

    MENU = [
        ("1", "Add bus"),
        ("2", "View all buses"),
        ("3", "Search buses by route"),
        ("4", "Show seat map of a bus"),
        ("5", "Book a ticket"),
        ("6", "Cancel a booking"),
        ("7", "View booking details"),
        ("8", "Reports (bookings & revenue)"),
        ("0", "Exit"),
    ]

    def __init__(self, system):
        self.system = system

    def run(self):
        handlers = {
            "1": self.add_bus,
            "2": self.view_buses,
            "3": self.search_buses,
            "4": self.show_seat_map,
            "5": self.book_ticket,
            "6": self.cancel_booking,
            "7": self.view_booking,
            "8": self.reports,
        }
        print(f"\nWelcome to {self.system.company_name}!")
        while True:
            self.show_menu()
            choice = input("Enter your choice: ").strip()
            if choice == "0":
                print("Thank you for using the system. Safe journey!")
                break
            handler = handlers.get(choice)
            if handler is None:
                print("  ! Invalid choice, please try again.")
                continue
            try:
                handler()
            except ReservationError as error:
                print(f"  ! {error}")
            except ValueError as error:
                print(f"  ! {error}")

    def show_menu(self):
        print("\n" + "=" * 46)
        print(f"  {self.system.company_name.upper()} - MAIN MENU")
        print("=" * 46)
        for key, label in self.MENU:
            print(f"  {key}. {label}")

    @staticmethod
    def _print_bus_table(buses, title=None):
        if title:
            print(f"\n{title}")
        if not buses:
            print("  No buses to show.")
            return
        header = f"{'Bus ID':<6}{'Route':<24}{'Type':<12}{'Dep.':<8}{'Fare':<13}{'Seats'}"
        print(header)
        print("-" * len(header))
        for bus in buses:
            print(bus)

    # ---- menu actions ----
    def add_bus(self):
        print("\n-- Add New Bus --")
        bus_id = ask_nonempty("Bus ID (e.g. B101): ").upper()
        route = ask_nonempty("Route (e.g. Delhi - Jaipur): ")
        departure = ask_nonempty("Departure time (e.g. 08:30): ")
        base_fare = ask_int("Base fare (Rs.): ", minimum=1)
        total_seats = ask_int("Total seats (1 to 40): ", minimum=1)
        if total_seats > 40:
            raise ReservationError("A bus cannot have more than 40 seats here.")

        print("  Bus types: 1. Standard   2. AC   3. Sleeper")
        bus_type = ask_int("Choose bus type: ", minimum=1)
        bus_classes = {1: Bus, 2: AC_Bus, 3: SleeperBus}
        if bus_type not in bus_classes:
            raise ReservationError("Invalid bus type choice.")

        bus = bus_classes[bus_type](bus_id, route, departure, base_fare, total_seats)
        self.system.add_bus(bus)
        print(f"  Bus {bus_id} added with fare Rs.{bus.fare:.2f}.")

    def view_buses(self):
        self._print_bus_table(self.system.all_buses(), "-- All Buses --")

    def search_buses(self):
        keyword = ask_nonempty("Enter route keyword (e.g. Delhi): ")
        self._print_bus_table(self.system.search_buses(keyword),
                              f"-- Buses matching '{keyword}' --")

    def show_seat_map(self):
        bus = self.system.get_bus(ask_nonempty("Bus ID: ").upper())
        bus.show_seat_map()
        print(f"  Free seats: {bus.free_seats()}")

    def book_ticket(self):
        print("\n-- Book a Ticket --")
        bus = self.system.get_bus(ask_nonempty("Bus ID: ").upper())
        print(f"  {bus.route} | {bus.bus_type} | Rs.{bus.fare:.2f} per seat")
        print(f"  Free seats: {bus.free_seats()}")

        name = ask_nonempty("Passenger name: ")
        age = ask_age("Passenger age: ")
        phone = input("Passenger phone (optional): ").strip()
        seat_no = ask_int("Seat number: ", minimum=1)

        passenger = Passenger(name, age, phone)
        booking = self.system.book_ticket(bus.bus_id, passenger, seat_no)
        print("\n" + booking.ticket())

    def cancel_booking(self):
        booking_id = ask_int("Booking ID to cancel: ", minimum=1)
        booking = self.system.find_booking(booking_id)
        print(f"  {booking.passenger.name} | Bus {booking.bus.bus_id} | Seat {booking.seat_no}")
        if ask_yes_no("Cancel this booking?"):
            self.system.cancel_booking(booking_id)
            print("  Booking cancelled and seat released.")
        else:
            print("  Cancellation aborted.")

    def view_booking(self):
        booking_id = ask_int("Booking ID: ", minimum=1)
        booking = self.system.find_booking(booking_id)
        print("\n" + booking.ticket())
        if booking.is_cancelled:
            print("  STATUS: CANCELLED")
        else:
            print("  STATUS: CONFIRMED")

    def reports(self):
        active = self.system.active_bookings()
        print("\n-- Reports --")
        print(f"  Total buses          : {len(self.system.all_buses())}")
        print(f"  Active bookings      : {len(active)}")
        print(f"  Total revenue        : Rs.{self.system.total_revenue():.2f}")
        for bus in self.system.all_buses():
            print(f"  Bus {bus.bus_id:<6} booked {bus.booked_count()}/{bus.total_seats} seats")


# ============================================================
#  SAMPLE DATA & PROGRAM START
# ============================================================
def load_sample_data(system):
    system.add_bus(Bus("B101", "Delhi - Jaipur", "08:30", 500, 20))
    system.add_bus(AC_Bus("B102", "Delhi - Agra", "10:00", 400, 16))
    system.add_bus(SleeperBus("B103", "Jaipur - Udaipur", "21:00", 700, 12))


if __name__ == "__main__":
    system = ReservationSystem("City Express Bus Service")
    load_sample_data(system)
    ReservationApp(system).run()
