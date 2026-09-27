#include <unity.h>

#include <map>
#include <string>

#include "progress.h"

using srs::Grade;
using srs::Stage;

namespace {

class Memory : public core::Storage {
public:
    bool load(const char* name, std::string& text) override
    {
        const auto found = files.find(name);
        if (found == files.end()) {
            return false;
        }
        text = found->second;
        return true;
    }
    bool save(const char* name, const std::string& text) override
    {
        if (failSaves) {
            return false;
        }
        files[name] = text;
        return true;
    }
    bool append(const char* name, const std::string& line) override
    {
        files[name] += line + "\n";
        return true;
    }

    std::map<std::string, std::string> files;
    bool failSaves = false;
};

size_t lineCount(const std::string& text)
{
    size_t n = 0;
    for (char c : text) {
        if (c == '\n') {
            ++n;
        }
    }
    return n;
}

}  // namespace

void setUp() {}
void tearDown() {}

void test_empty_store()
{
    Memory memory;
    progress::Store store(memory);
    store.load();
    TEST_ASSERT_EQUAL_UINT(0, store.seen());
    TEST_ASSERT_EQUAL_INT(static_cast<int>(Stage::New), static_cast<int>(store.get(0x1234).stage));
    TEST_ASSERT_EQUAL_UINT(0, store.dueOn(5));
}

void test_answers_survive_a_restart_through_the_log()
{
    Memory memory;
    {
        progress::Store store(memory);
        store.load();
        store.record(0xAAAA0001, Grade::Good, 1);
        store.record(0xAAAA0001, Grade::Good, 1);
        store.record(0xBBBB0002, Grade::Again, 1);
        TEST_ASSERT_EQUAL_UINT(2, store.seen());
        TEST_ASSERT_EQUAL_UINT(1, store.learnt());
    }
    TEST_ASSERT_EQUAL_UINT(3, lineCount(memory.files["reviews.log"]));
    TEST_ASSERT_TRUE(memory.files.find("progress.txt") == memory.files.end());

    progress::Store again(memory);
    again.load();
    TEST_ASSERT_EQUAL_UINT(2, again.seen());
    const srs::Card a = again.get(0xAAAA0001);
    TEST_ASSERT_EQUAL_INT(static_cast<int>(Stage::Review), static_cast<int>(a.stage));
    TEST_ASSERT_EQUAL_UINT(2, a.due);
    const srs::Card b = again.get(0xBBBB0002);
    TEST_ASSERT_EQUAL_INT(static_cast<int>(Stage::Learning), static_cast<int>(b.stage));
    TEST_ASSERT_EQUAL_UINT(1, again.dueOn(1));
    TEST_ASSERT_EQUAL_UINT(2, again.dueOn(2));
}

void test_checkpoint_folds_the_log_into_the_snapshot()
{
    Memory memory;
    progress::Store store(memory);
    store.load();
    store.record(0x00000010, Grade::Good, 3);
    store.record(0x00000010, Grade::Good, 3);
    store.record(0xFFFFFFF0, Grade::Good, 3);
    TEST_ASSERT_TRUE(store.checkpoint());
    TEST_ASSERT_EQUAL_STRING("", memory.files["reviews.log"].c_str());
    TEST_ASSERT_EQUAL_STRING("00000010 4 1 250 2 0 0\nfffffff0 3 0 250 1 1 0\n", memory.files["progress.txt"].c_str());

    store.record(0x00000010, Grade::Good, 4);
    progress::Store again(memory);
    again.load();
    TEST_ASSERT_EQUAL_UINT(3, again.get(0x00000010).interval);
    TEST_ASSERT_EQUAL_UINT(7, again.get(0x00000010).due);
    TEST_ASSERT_EQUAL_UINT(1, again.get(0xFFFFFFF0).streak);
}

void test_the_log_folds_itself_when_it_grows()
{
    Memory memory;
    progress::Store store(memory);
    store.load();
    for (int i = 0; i < 199; ++i) {
        store.record(0x100 + static_cast<uint32_t>(i % 7), Grade::Hard, 1);
    }
    TEST_ASSERT_EQUAL_UINT(199, lineCount(memory.files["reviews.log"]));
    store.record(0x100, Grade::Hard, 1);
    TEST_ASSERT_EQUAL_UINT(0, lineCount(memory.files["reviews.log"]));
    TEST_ASSERT_EQUAL_UINT(7, lineCount(memory.files["progress.txt"]));
}

void test_damaged_files_cost_lines_not_everything()
{
    Memory memory;
    memory.files["progress.txt"] =
        "00000010 4 1 250 2 0 0\n"
        "this is not a card\n"
        "00000011 4 1 250 9 0 0\n"   // no such stage
        "00000012 4 1 250 2 0\n"     // a number missing
        "\r\n"
        "00000013 9 5 200 2 0 3\r\n";
    memory.files["reviews.log"] =
        "5 00000010 2\n"
        "rubbish\n"
        "5 00000014 7\n"   // no such grade
        "5 00000014 0";    // no line ending at the end of the file
    progress::Store store(memory);
    store.load();
    TEST_ASSERT_EQUAL_UINT(3, store.seen());
    // due on day 4, answered on day 5: the day of lateness earns a little extra
    TEST_ASSERT_EQUAL_UINT(4, store.get(0x10).interval);
    TEST_ASSERT_EQUAL_UINT(9, store.get(0x10).due);
    TEST_ASSERT_EQUAL_UINT(3, store.get(0x13).lapses);
    TEST_ASSERT_EQUAL_INT(static_cast<int>(Stage::New), static_cast<int>(store.get(0x11).stage));
    TEST_ASSERT_EQUAL_INT(static_cast<int>(Stage::New), static_cast<int>(store.get(0x12).stage));
    TEST_ASSERT_EQUAL_INT(static_cast<int>(Stage::Learning), static_cast<int>(store.get(0x14).stage));
}

void test_a_failed_save_keeps_the_log()
{
    Memory memory;
    progress::Store store(memory);
    store.load();
    store.record(0x20, Grade::Good, 1);
    memory.failSaves = true;
    TEST_ASSERT_FALSE(store.checkpoint());
    TEST_ASSERT_EQUAL_UINT(1, lineCount(memory.files["reviews.log"]));
    TEST_ASSERT_EQUAL_UINT(1, store.seen());
}

void test_reset()
{
    Memory memory;
    progress::Store store(memory);
    store.load();
    store.record(0x30, Grade::Good, 1);
    store.checkpoint();
    store.record(0x31, Grade::Good, 1);
    store.reset();
    TEST_ASSERT_EQUAL_UINT(0, store.seen());
    progress::Store again(memory);
    again.load();
    TEST_ASSERT_EQUAL_UINT(0, again.seen());
}

int main(int, char**)
{
    UNITY_BEGIN();
    RUN_TEST(test_empty_store);
    RUN_TEST(test_answers_survive_a_restart_through_the_log);
    RUN_TEST(test_checkpoint_folds_the_log_into_the_snapshot);
    RUN_TEST(test_the_log_folds_itself_when_it_grows);
    RUN_TEST(test_damaged_files_cost_lines_not_everything);
    RUN_TEST(test_a_failed_save_keeps_the_log);
    RUN_TEST(test_reset);
    return UNITY_END();
}
