import json
from unittest import TestCase
from unittest.mock import ANY

from aiohttp_underscore_apis.apis.filter_path import filter_path

# json.org/example.html
json_example = """\
{"web-app": {
  "servlet": [
    {
      "servlet-name": "cofaxCDS",
      "servlet-class": "org.cofax.cds.CDSServlet",
      "init-param": {
        "configGlossary:installationAt": "Philadelphia, PA",
        "configGlossary:adminEmail": "ksm@pobox.com",
        "configGlossary:poweredBy": "Cofax",
        "configGlossary:poweredByIcon": "/images/cofax.gif",
        "configGlossary:staticPath": "/content/static",
        "templateProcessorClass": "org.cofax.WysiwygTemplate",
        "templateLoaderClass": "org.cofax.FilesTemplateLoader",
        "templatePath": "templates",
        "templateOverridePath": "",
        "defaultListTemplate": "listTemplate.htm",
        "defaultFileTemplate": "articleTemplate.htm",
        "useJSP": false,
        "jspListTemplate": "listTemplate.jsp",
        "jspFileTemplate": "articleTemplate.jsp",
        "cachePackageTagsTrack": 200,
        "cachePackageTagsStore": 200,
        "cachePackageTagsRefresh": 60,
        "cacheTemplatesTrack": 100,
        "cacheTemplatesStore": 50,
        "cacheTemplatesRefresh": 15,
        "cachePagesTrack": 200,
        "cachePagesStore": 100,
        "cachePagesRefresh": 10,
        "cachePagesDirtyRead": 10,
        "searchEngineListTemplate": "forSearchEnginesList.htm",
        "searchEngineFileTemplate": "forSearchEngines.htm",
        "searchEngineRobotsDb": "WEB-INF/robots.db",
        "useDataStore": true,
        "dataStoreClass": "org.cofax.SqlDataStore",
        "redirectionClass": "org.cofax.SqlRedirection",
        "dataStoreName": "cofax",
        "dataStoreDriver": "com.microsoft.jdbc.sqlserver.SQLServerDriver",
        "dataStoreUrl": "jdbc:microsoft:sqlserver://LOCALHOST:1433;DatabaseName=goon",
        "dataStoreUser": "sa",
        "dataStorePassword": "dataStoreTestQuery",
        "dataStoreTestQuery": "SET NOCOUNT ON;select test='test';",
        "dataStoreLogFile": "/usr/local/tomcat/logs/datastore.log",
        "dataStoreInitConns": 10,
        "dataStoreMaxConns": 100,
        "dataStoreConnUsageLimit": 100,
        "dataStoreLogLevel": "debug",
        "maxUrlLength": 500}},
    {
      "servlet-name": "cofaxEmail",
      "servlet-class": "org.cofax.cds.EmailServlet",
      "init-param": {
      "mailHost": "mail1",
      "mailHostOverride": "mail2"}},
    {
      "servlet-name": "cofaxAdmin",
      "servlet-class": "org.cofax.cds.AdminServlet"},

    {
      "servlet-name": "fileServlet",
      "servlet-class": "org.cofax.cds.FileServlet"},
    {
      "servlet-name": "cofaxTools",
      "servlet-class": "org.cofax.cms.CofaxToolsServlet",
      "init-param": {
        "templatePath": "toolstemplates/",
        "log": 1,
        "logLocation": "/usr/local/tomcat/logs/CofaxTools.log",
        "logMaxSize": "",
        "dataLog": 1,
        "dataLogLocation": "/usr/local/tomcat/logs/dataLog.log",
        "dataLogMaxSize": "",
        "removePageCache": "/content/admin/remove?cache=pages&id=",
        "removeTemplateCache": "/content/admin/remove?cache=templates&id=",
        "fileTransferFolder": "/usr/local/tomcat/webapps/content/fileTransferFolder",
        "lookInContext": 1,
        "adminGroupID": 4,
        "betaServer": true}}],
  "servlet-mapping": {
    "cofaxCDS": "/",
    "cofaxEmail": "/cofaxutil/aemail/*",
    "cofaxAdmin": "/admin/*",
    "fileServlet": "/static/*",
    "cofaxTools": "/tools/*"},

  "taglib": {
    "taglib-uri": "cofax.tld",
    "taglib-location": "/WEB-INF/tlds/cofax.tld"}}}
"""  # noqa: E501


class FilterPathTest(TestCase):
    def test_filter_path(self):

        # Check if TypeError is raised for an invalid argument
        with self.assertRaises(TypeError):
            filter_path(1, "")  # type: ignore[arg-type]

        # Check if filtering an empty list or dict always does nothing but
        # returns a different instance.
        for expressions in (
            "",
            "*",
            "-*",
            ",",
            ",,",
            ",+*,-*",
            ",test,test",
        ):
            with self.subTest(filter_expressions=expressions):
                filtered = filter_path([], *expressions.split(","))
                self.assertEqual(filtered, [])
                self.assertIsNot(filtered, [])

                filtered = filter_path({}, *expressions.split(","))
                self.assertEqual(filtered, {})
                self.assertIsNot(filtered, {})

        # Check filtering of a list: only ``, `*`, `+`, and `+*` preserve the
        # items.
        for source, expressions, expected in (
            ([1, 2, 3], "", [1, 2, 3]),
            ([1, 2, 3], "*", [1, 2, 3]),
            ([1, 2, 3], "+", [1, 2, 3]),
            ([1, 2, 3], "+*", [1, 2, 3]),
            ([1, 2, 3], ",", [1, 2, 3]),
            ([1, 2, 3], ",*", [1, 2, 3]),
            ([1, 2, 3], ",+,", [1, 2, 3]),
            ([1, 2, 3], "-", []),
            ([1, 2, 3], "-*", []),
            ([1, 2, 3], " ", []),
            # Filter-out should always have precedence over filter-in because
            # it is applied first.
            ([1, 2, 3], "*,-*", []),
            ([1, 2, 3], ",+*,-*", []),
            ([1, 2, 3], ",-*,+*", []),
        ):
            with self.subTest(filter_expressions=expressions):
                filtered = filter_path(source, *expressions.split(","))
                self.assertEqual(filtered, expected)
                self.assertEqual(source, source)

        source = json.loads(json_example)

        # Check if no filtering expressions return an unmodified copy
        filtered = filter_path(source)
        self.assertDictEqual(filtered, source)
        self.assertIsNot(filtered, source)

        # Check if empty filter expressions return an unmodified copy
        for filter_expressions in (
            ("",),
            ("+",),
            ("", ""),
            ("", "+"),
        ):
            filtered = filter_path(source, *filter_expressions)
            self.assertDictEqual(filtered, source)
            self.assertIsNot(filtered, source)

        # Check if empty exclusive filter expressions return an empty dict
        for filter_expressions in (
            ("-",),
            ("-", "-"),
        ):
            filtered = filter_path(source, *filter_expressions)
            self.assertDictEqual(filtered, {})
            self.assertNotEqual(filtered, source)

        # Check filtering of a dict with a double-asterisk matcher
        filtered = filter_path(source, "**.servlet-name")
        self.assertDictEqual(filtered, {"web-app": {"servlet": ANY}})
        self.assertSequenceEqual(
            filtered["web-app"]["servlet"],
            [
                {"servlet-name": "cofaxCDS"},
                {"servlet-name": "cofaxEmail"},
                {"servlet-name": "cofaxAdmin"},
                {"servlet-name": "fileServlet"},
                {"servlet-name": "cofaxTools"},
            ],
        )

        # Check if filter-out has precedence over filter-in for dicts
        filtered = filter_path(source, "-*", "**.servlet-name")
        self.assertEqual(filtered, {})

        filtered = filter_path(source, "*", "-*", "**.servlet-name")
        self.assertEqual(filtered, {})

        filtered = filter_path(source, "-*", "**.servlet-name", "*")
        self.assertEqual(filtered, {})

        # Check if `cofax*` matches keys starting with `cofax`
        filtered = filter_path(source, "*.servlet-mapping", "-**.cofax*")
        self.assertDictEqual(
            filtered["web-app"]["servlet-mapping"],
            {"fileServlet": "/static/*"},
        )

        # Check if `cofax` doesn't match keys starting with `cofax`
        filtered = filter_path(source, "*.servlet-mapping", "-**.cofax")
        self.assertDictEqual(
            filtered["web-app"]["servlet-mapping"],
            {
                "cofaxAdmin": "/admin/*",
                "cofaxCDS": "/",
                "cofaxEmail": "/cofaxutil/aemail/*",
                "cofaxTools": "/tools/*",
                "fileServlet": "/static/*",
            },
        )

        # Check if the exclusive filter has precedence
        filtered = filter_path(source, "**.cofax*", "-**.*Email")
        self.assertDictEqual(
            filtered["web-app"]["servlet-mapping"],
            {
                "cofaxAdmin": "/admin/*",
                "cofaxCDS": "/",
                "cofaxTools": "/tools/*",
            },
        )
