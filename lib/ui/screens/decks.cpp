// Decks. A place holder until the screen is written.
#include "../screens.h"

namespace ui {

namespace {

class DecksScreen : public Screen {
public:
    void key(App& app, const Key&) override { app.show(ScreenId::Menu); }

    void draw(App& app, Canvas& c) override
    {
        const Theme& t = app.theme();
        drawFrame(c, t, "Decks", "", "Any key: back", "");
        drawMessage(c, t, "Not written yet", t.dim);
    }
};

}  // namespace

std::unique_ptr<Screen> makeDecksScreen()
{
    return std::unique_ptr<Screen>(new DecksScreen());
}

}  // namespace ui
