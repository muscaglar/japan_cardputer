// The memory card. It holds what does not fit into the device: sound clips now, the dictionary
// and the owner's own packs later. The app works without one.
#pragma once

#include <FS.h>

#include <cstdint>

// Mounts the card. Called once at start. false if there is none or it cannot be read.
bool cardBegin();

// Whether a card is mounted.
bool cardReady();

// The files on the card. Paths start with "/". Only valid while cardReady().
fs::FS& cardFiles();

uint64_t cardBytesTotal();
uint64_t cardBytesUsed();
