// The screens of the app. Each is built by a factory so that app.cpp needs no details.
#pragma once

#include <memory>

#include "app.h"

namespace ui {

std::unique_ptr<Screen> makeHomeScreen();
std::unique_ptr<Screen> makeMenuScreen();
std::unique_ptr<Screen> makeKanaScreen();
std::unique_ptr<Screen> makeSettingsScreen();
std::unique_ptr<Screen> makeCardsScreen();
std::unique_ptr<Screen> makeSummaryScreen();

}  // namespace ui
