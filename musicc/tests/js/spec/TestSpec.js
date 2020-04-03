describe("The sidebar", function () {
   testArea = null
   beforeEach(function () {
      testArea = $('<div id="test-area"/>').appendTo('body')
   });

   afterEach(function () {
      $('body > #test-area').remove();
   });

   it("knows all the binary comparators", function () {
      binaryComparators = ["=", "==", ">", "<"]
      notBinaryComparators = ["+", "-", "=>", "= <", "INCLUDE"]
      binaryComparators.forEach((val) => {
         expect(isBinaryComparator(val)).toBe(true);
      });
      notBinaryComparators.forEach((val) => {
         expect(isBinaryComparator(val)).toBe(false);
      });
   });

   it("can create a json form based on a json schema", function () {
      testArea.append('<div id="sidebar"><form/></div>')

      createJsonForm(test_schema);
      expect($("label.title").length).toBe(8);

      // Description should have a text input
      expect($('label[value=Description]').siblings(".controls").find("input").attr("type")).toBe("text")

      // Selectors should have all enum values
      countryCodeList = $('label[value=CountryCode]').siblings(".controls").find("select").text().trim().split(" ")
      expect(countryCodeList).toEqual(test_schema.properties.CountryCode.properties.value.enum)

      // An object with multiple properties should have a field for each property
      expect($('label[value=RealWorldMap__value]').length).toBe(1)
      expect($('label[value=RealWorldMap__mapDataValidDateTime]').length).toBe(1)

      // Boolean fields should have checkboxes
      expect($('label[value=RepresentsADASTest]').siblings(".controls").find("input").attr("type")).toBe("checkbox")

      // Array field labels should have an array class and a user friendly name
      expect($('label[value="Regulations__Regulation"]').hasClass("array")).toBe(true)
      expect($('label[value="Regulations__Regulation"]').text()).toBe("Regulations")

      // CustomMetadata should not appear
      expect($('label[value=CustomMetadata]').length).toBe(0)

      // maxLength fields should be reflected in text inputs
      expect($('label[value=label]').siblings(".controls").find("input").attr("maxLength")).toBe(test_schema.properties.label.maxLength)

      // datetime fields should have datetime inputs
      expect($('label[value=updateDateTime]').siblings(".controls").find("input").attr("type")).toBe("datetime-local")
   });

   it("can add a query to the search bar", function () {
      testArea.append('<div id="sidebar"><form/></div>');
      testArea.append('<input type="text" id="search-bar">');

      initialiseSidebar(test_schema);

      // Standard input with enter button
      $('label[value=Description]').siblings(".controls").find("input").val("my test data");
      $('label[value=Description]').siblings(".controls").find("input").trigger($.Event("keypress", { 'which': 13 }));
      expect($("#search-bar").val()).toBe(`Description = "my test data"`)

      // Select input with AND button
      $('label[value=CountryCode]').siblings(".controls").find("select").val('CH')
      $($('label[value=CountryCode]').siblings(".controls").find("button")[1]).click()
      expect($("#search-bar").val()).toBe(`Description = "my test data" AND CountryCode = "CH"`)

      // Array input with AND button
      $('label[value=Regulations__Regulation]').siblings(".controls").find("input").val('a_regulation')
      $($('label[value=Regulations__Regulation]').siblings(".controls").find("button")[1]).click()
      expect($("#search-bar").val()).toBe(`Description = "my test data" AND CountryCode = "CH" AND Regulations__Regulation INCLUDES "a_regulation"`)

      // Boolean input with OR button
      $('label[value=RepresentsADASTest]').siblings(".controls").find("input").click()
      $($('label[value=RepresentsADASTest]').siblings(".controls").find("button")[0]).click()
      expect($("#search-bar").val()).toBe(`Description = "my test data" AND CountryCode = "CH" AND Regulations__Regulation INCLUDES "a_regulation" OR RepresentsADASTest = "True"`)
   });

   it("minimises the sidebar when the button is clicked", function () {
      testArea.append('<div id="sidebar"><form/></div>');
      testArea.append('<input type="text" id="search-bar">');
      $(`<div id="sidebar-collapse-controls">
         <button id="sidebar-collapse-controls-minimise">
            <div class="arrow left"></div>
         </button>
      </div>`).appendTo(testArea)
      initialiseSidebar(test_schema);

      expect($("#sidebar").hasClass("minimised-sidebar")).toBe(false)
      expect($("#sidebar-collapse-controls-minimise .arrow").hasClass("left")).toBe(true)
      expect($("#sidebar-collapse-controls-minimise .arrow").hasClass("right")).toBe(false)
      toggleMinimisedSidebar()
      expect($("#sidebar").hasClass("minimised-sidebar")).toBe(true)
      expect($("#sidebar-collapse-controls-minimise .arrow").hasClass("left")).toBe(false)
      expect($("#sidebar-collapse-controls-minimise .arrow").hasClass("right")).toBe(true)
   });

   test_schema = {
      "type": "object",
      "properties": {
         "Description": {
            "type": "object",
            "properties": {
               "value": {
                  "type": "string",
                  "maxLength": "2048"
               }
            }
         },
         "CountryCode": {
            "type": "object",
            "properties": {
               "value": {
                  "type": "string",
                  "enum": [
                     "GB",
                     "DE",
                     "CH",
                     "AT",
                     "IE"
                  ]
               }
            }
         },
         "RealWorldMap": {
            "type": "object",
            "properties": {
               "value": {
                  "type": "boolean"
               },
               "mapDataValidDateTime": {
                  "type": "datetime-local"
               }
            }
         },
         "RepresentsADASTest": {
            "type": "object",
            "properties": {
               "value": {
                  "type": "boolean"
               }
            }
         },
         "Regulations": {
            "type": "object",
            "array": true,
            "properties": {
               "Regulation": {
                  "type": "object",
                  "properties": {
                     "value": {
                        "type": "string"
                     }
                  }
               }
            }
         },
         "CustomMetadata": {
            "type": "object",
            "array": true,
            "properties": {
               "CustomTag": {
                  "type": "object",
                  "properties": {
                     "name": {
                        "type": "string"
                     },
                     "value": {
                        "type": "string"
                     }
                  }
               }
            }
         },
         "label": {
            "type": "string",
            "maxLength": "50"
         },
         "updateDateTime": {
            "type": "datetime-local"
         }
      }
   }
});