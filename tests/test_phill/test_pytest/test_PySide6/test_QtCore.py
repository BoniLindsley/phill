#!/usr/bin/env python3

# External dependencies.
import PySide6.QtCore


class TestPyside6Fixture:
    def test_does_not_require_q_core_application_to_be_created(
        self, pyside6: None
    ) -> None:
        del pyside6

    def test_cleans_up_q_core_application(self, pyside6: None) -> None:
        del pyside6
        PySide6.QtCore.QCoreApplication()

    def test_another_test_can_create_another_application(
        self, pyside6: None
    ) -> None:
        del pyside6
        PySide6.QtCore.QCoreApplication()


class TestQCoreApplication:
    def test_cleans_up_q_core_application(
        self, q_core_application: PySide6.QtCore.QCoreApplication
    ) -> None:
        del q_core_application

    def test_another_test_can_create_another_application(
        self, q_core_application: PySide6.QtCore.QCoreApplication
    ) -> None:
        del q_core_application
