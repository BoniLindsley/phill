#!/usr/bin/env python3

# External dependencies.
import PySide6.QtGui
import PySide6.QtWidgets

# Internal packages.
import phill.PySide6.QtCore
import phill.PySide6.QtWidgets


class TestOffscreenSystemTrayIcon:
    def test_can_default_construct(
        self, q_application: PySide6.QtWidgets.QApplication
    ) -> None:
        del q_application
        phill.PySide6.QtWidgets.OffscreenSystemTrayIcon()

    def test_init_accepts_new_icon(
        self, q_application: PySide6.QtWidgets.QApplication
    ) -> None:
        del q_application
        icon = PySide6.QtGui.QIcon()
        phill.PySide6.QtWidgets.OffscreenSystemTrayIcon(icon)

    def test_get_icon(
        self, q_application: PySide6.QtWidgets.QApplication
    ) -> None:
        del q_application
        pixmap = PySide6.QtGui.QPixmap(1, 1)
        icon = PySide6.QtGui.QIcon(pixmap)
        tray_icon = phill.PySide6.QtWidgets.OffscreenSystemTrayIcon(icon)
        assert tray_icon.icon().cacheKey() == icon.cacheKey()

    def test_set_icon(
        self, q_application: PySide6.QtWidgets.QApplication
    ) -> None:
        del q_application
        tray_icon = phill.PySide6.QtWidgets.OffscreenSystemTrayIcon()
        icon = PySide6.QtGui.QIcon()
        tray_icon.setIcon(icon)
        assert tray_icon.icon().cacheKey() == icon.cacheKey()
