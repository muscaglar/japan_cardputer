// Kana chart. A place holder until the screen is written.
#include "../screens.h"

namespace ui {

namespace {

class ChartScreen : public Screen {
public:
    void key(App& app, const Key&) override { app.show(ScreenId::Menu); }

    void draw(App& app, Canvas& c) override
    {
        const Theme& t = app.theme();
        drawFrame(c, t, "Kana chart", "", "Any key: back", "");
        drawMessage(c, t, "Not written yet", t.dim);
    }
};

}  // namespace

std::unique_ptr<Screen> makeChartScreen()
{
    return std::unique_ptr<Screen>(new ChartScreen());
}

}  // namespace ui
