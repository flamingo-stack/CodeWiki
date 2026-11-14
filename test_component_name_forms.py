"""A component the model names instead of numbering resolves by its exact spellings, and nothing else does."""

from codewiki.src.be.cluster_modules import component_name_forms, normalize_component_id_list

LIB = "openframe-oss-lib.openframe-external-api-service-core.src.main.java.com.openframe.external"
COMPONENTS = {
    f"{LIB}.controller.CustomerController::CustomerController": object(),
    f"{LIB}.controller.DeviceController::DeviceController": object(),
    f"{LIB}.dto.ticket.TicketsResponse::TicketsResponse": object(),
    f"{LIB}.dto.ticket.TicketsResponse::TicketsResponseItem": object(),
    "app.main::run": object(),
}
ID_TO_FQDN = {i: fqdn for i, fqdn in enumerate(sorted(COMPONENTS))}


def test_the_module_path_names_every_component_of_its_file():
    # The form openframe-oss-tenant's run returned for 30 components of one sub-module (2026-11-14).
    resolved, normalized, failed = normalize_component_id_list(
        [f"{LIB}.controller.CustomerController", f"{LIB}.dto.ticket.TicketsResponse"], ID_TO_FQDN, components=COMPONENTS
    )
    assert resolved == [
        f"{LIB}.controller.CustomerController::CustomerController",
        f"{LIB}.dto.ticket.TicketsResponse::TicketsResponse",
        f"{LIB}.dto.ticket.TicketsResponse::TicketsResponseItem",
    ]
    assert (normalized, failed) == (2, 0)


def test_the_id_and_its_dotted_spelling_resolve_to_that_component():
    resolved, _, failed = normalize_component_id_list(
        [f"{LIB}.controller.DeviceController::DeviceController", f"{LIB}.controller.DeviceController.DeviceController"],
        ID_TO_FQDN,
        components=COMPONENTS,
    )
    assert resolved == [f"{LIB}.controller.DeviceController::DeviceController"]
    assert failed == 0


def test_numbers_still_resolve_and_a_component_named_twice_is_listed_once():
    number = next(i for i, f in ID_TO_FQDN.items() if f == "app.main::run")
    resolved, _, failed = normalize_component_id_list([number, "app.main::run", str(number)], ID_TO_FQDN, components=COMPONENTS)
    assert resolved == ["app.main::run"]
    assert failed == 0


def test_anything_else_is_not_guessed():
    resolved, _, failed = normalize_component_id_list(
        ["CustomerController", f"{LIB}.controller", "controller.CustomerController", 999], ID_TO_FQDN, components=COMPONENTS
    )
    assert resolved == []
    assert failed == 4


def test_without_the_registry_only_numbers_resolve():
    resolved, _, failed = normalize_component_id_list([f"{LIB}.controller.CustomerController", 0], ID_TO_FQDN)
    assert resolved == [ID_TO_FQDN[0]]
    assert failed == 1


def test_forms_of_an_id_without_a_name_part_are_the_id_alone():
    assert component_name_forms({"plain.module": object()}) == {"plain.module": ["plain.module"]}
