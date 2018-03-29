#include "dl.h"

using namespace slack;

static void
slack_test_dl_construct()
{
	auto dl = new Dl ("some", "mirror", 1, NULL, NULL);

	g_assert_cmpstr (dl->get_name (), ==, "some");
	g_assert_cmpstr (dl->get_mirror (), ==, "mirror");
	g_assert_cmpuint (dl->get_order (), ==, 1);
	g_assert_false (dl->is_blacklisted ("pattern"));

	delete dl;
}

int main(int argc, char *argv[])
{
	g_test_init(&argc, &argv, NULL);

	g_test_add_func("/slack/dl/construct", slack_test_dl_construct);

	return g_test_run();
}
