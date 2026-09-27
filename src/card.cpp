#include "card.h"

#include <SD.h>
#include <SPI.h>

namespace {

// The same pins on the Cardputer, the v1.1 and the ADV.
constexpr int kSck  = 40;
constexpr int kMiso = 39;
constexpr int kMosi = 14;
constexpr int kCs   = 12;

bool mounted = false;

}  // namespace

bool cardBegin()
{
    SPI.begin(kSck, kMiso, kMosi, kCs);
    mounted = SD.begin(kCs, SPI, 25000000) && SD.cardType() != CARD_NONE;
    return mounted;
}

bool cardReady()
{
    return mounted;
}

fs::FS& cardFiles()
{
    return SD;
}

uint64_t cardBytesTotal()
{
    return mounted ? SD.totalBytes() : 0;
}

uint64_t cardBytesUsed()
{
    return mounted ? SD.usedBytes() : 0;
}
