// Small text files that survive a restart. The device keeps them in its flash file system, the
// simulator in memory or in the browser.
#pragma once

#include <string>

namespace core {

class Storage {
public:
    virtual ~Storage() = default;
    virtual bool load(const char* name, std::string& text)         = 0;
    virtual bool save(const char* name, const std::string& text)   = 0;
    virtual bool append(const char* name, const std::string& line) = 0;  // adds the line and a newline
};

}  // namespace core
