from instant_translator.ui.popup_window import PopupWindow


def test_popup_window_reports_new_width_on_resize(qtbot):
    widths = []
    popup = PopupWindow(on_width_changed=widths.append)
    qtbot.addWidget(popup)

    popup.show_result("译文")
    popup.resize(560, popup.height())
    qtbot.wait(50)

    assert widths[-1] == 560
