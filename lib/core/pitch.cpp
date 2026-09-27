#include "pitch.h"

namespace pitch {

std::vector<bool> heights(int beatCount, int accent)
{
    std::vector<bool> out;
    if (beatCount <= 0 || accent < 0 || accent > beatCount) {
        return out;
    }
    out.assign(static_cast<size_t>(beatCount), false);
    if (accent == 0) {
        for (int i = (beatCount > 1 ? 1 : 0); i < beatCount; ++i) {
            out[static_cast<size_t>(i)] = true;
        }
    } else if (accent == 1) {
        out[0] = true;
    } else {
        for (int i = 1; i < accent; ++i) {
            out[static_cast<size_t>(i)] = true;
        }
    }
    return out;
}

bool particleIsHigh(int accent)
{
    return accent == 0;
}

}  // namespace pitch
