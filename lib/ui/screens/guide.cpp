// Sounds. A place holder until the screen is written.
#include "../screens.h"

namespace ui {

namespace {

class GuideScreen : public Screen {
public:
    void key(App& app, const Key&) override { app.show(ScreenId::Menu); }

    void draw(App& app, Canvas& c) override
    {
        const Theme& t = app.theme();
        drawFrame(c, t, "Sounds", "", "Any key: back", "");
        drawMessage(c, t, "Not written yet", t.dim);
    }
};

}  // namespace

std::unique_ptr<Screen> makeGuideScreen()
{
    return std::unique_ptr<Screen>(new GuideScreen());
}

}  // namespace ui
