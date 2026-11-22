import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const addinDir = path.resolve(__dirname, "..");
const distDir = path.join(addinDir, "dist");

const DEV_BASE_URL = "https://localhost:3000";
const PROD_BASE_URL = (process.env.ADDIN_BASE_URL || "https://tamil-toolkit-word.vercel.app").replace(/\/+$/, "");
const ADDIN_VERSION = "2.3.0.0";
const ICON_VER = "2";
const ADDIN_ID = "9c2e4f11-88a3-4d9c-b244-1f7a30650283";

export function renderManifestXml(baseUrl) {
  const cleanUrl = baseUrl.replace(/\/+$/, "");
  const origin = new URL(cleanUrl).origin;

  return `<?xml version="1.0" encoding="UTF-8"?>
<OfficeApp xmlns="http://schemas.microsoft.com/office/appforoffice/1.1"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xmlns:bt="http://schemas.microsoft.com/office/officeappbasictypes/1.0"
           xmlns:ov="http://schemas.microsoft.com/office/taskpaneappversionoverrides"
           xsi:type="TaskPaneApp">
  <Id>${ADDIN_ID}</Id>
  <Version>${ADDIN_VERSION}</Version>
  <ProviderName>Tamil Toolkit</ProviderName>
  <DefaultLocale>en-US</DefaultLocale>
  <DisplayName DefaultValue="Tamil Toolkit">
    <Override Locale="ta-IN" Value="தமிழ் கருவி" />
  </DisplayName>
  <Description DefaultValue="100% client-side Tamil utility suite for Word: legacy font conversion, Unicode repair, Akara Varisai sorting, numerals, Tamil calendar, and syllabic hyphenation." />
  <IconUrl DefaultValue="${cleanUrl}/assets/icon-32.png?v=${ICON_VER}" />
  <HighResolutionIconUrl DefaultValue="${cleanUrl}/assets/icon-64.png?v=${ICON_VER}" />
  <SupportUrl DefaultValue="${cleanUrl}/support.html" />
  <AppDomains>
    <AppDomain>${origin}</AppDomain>
  </AppDomains>
  <Hosts>
    <Host Name="Document" />
  </Hosts>
  <Requirements>
    <Sets DefaultMinVersion="1.3">
      <Set Name="WordApi" MinVersion="1.3" />
    </Sets>
  </Requirements>
  <DefaultSettings>
    <SourceLocation DefaultValue="${cleanUrl}/index.html" />
  </DefaultSettings>
  <Permissions>ReadWriteDocument</Permissions>
  <VersionOverrides xmlns="http://schemas.microsoft.com/office/taskpaneappversionoverrides" xsi:type="VersionOverridesV1_0">
    <Hosts>
      <Host xsi:type="Document">
        <Runtimes>
          <Runtime resid="Taskpane.Url" lifetime="long" />
        </Runtimes>
        <DesktopFormFactor>
          <GetStarted>
            <Title resid="GetStarted.Title" />
            <Description resid="GetStarted.Description" />
            <LearnMoreUrl resid="Support.Url" />
          </GetStarted>
          <FunctionFile resid="Taskpane.Url" />
          <ExtensionPoint xsi:type="PrimaryCommandSurface">
            <CustomTab id="TamilToolkit.Tab">
              <Group id="TamilToolkit.SuiteGroup">
                <Label resid="SuiteGroup.Label" />
                <Icon>
                  <bt:Image size="16" resid="Icon.16" />
                  <bt:Image size="32" resid="Icon.32" />
                  <bt:Image size="80" resid="Icon.80" />
                </Icon>
                <Control xsi:type="Button" id="TamilToolkit.OpenTaskpaneBtn">
                  <Label resid="OpenTaskpane.Label" />
                  <Supertip>
                    <Title resid="OpenTaskpane.Label" />
                    <Description resid="OpenTaskpane.Tooltip" />
                  </Supertip>
                  <Icon>
                    <bt:Image size="16" resid="Icon.16" />
                    <bt:Image size="32" resid="Icon.32" />
                    <bt:Image size="80" resid="Icon.80" />
                  </Icon>
                  <Action xsi:type="ShowTaskpane">
                    <TaskpaneId>TamilToolkit.Taskpane</TaskpaneId>
                    <SourceLocation resid="Taskpane.Url" />
                  </Action>
                </Control>
                <Control xsi:type="Button" id="TamilToolkit.LiveTypingBtn">
                  <Label resid="LiveTyping.Label" />
                  <Supertip>
                    <Title resid="LiveTyping.Label" />
                    <Description resid="LiveTyping.Tooltip" />
                  </Supertip>
                  <Icon>
                    <bt:Image size="16" resid="Icon.Type.16" />
                    <bt:Image size="32" resid="Icon.Type.32" />
                    <bt:Image size="80" resid="Icon.Type.80" />
                  </Icon>
                  <Action xsi:type="ExecuteFunction">
                    <FunctionName>toggleLiveTypingCommand</FunctionName>
                  </Action>
                </Control>
                <Control xsi:type="Button" id="TamilToolkit.AutoConvertBtn">
                  <Label resid="AutoConvert.Label" />
                  <Supertip>
                    <Title resid="AutoConvert.Label" />
                    <Description resid="AutoConvert.Tooltip" />
                  </Supertip>
                  <Icon>
                    <bt:Image size="16" resid="Icon.Convert.16" />
                    <bt:Image size="32" resid="Icon.Convert.32" />
                    <bt:Image size="80" resid="Icon.Convert.80" />
                  </Icon>
                  <Action xsi:type="ExecuteFunction">
                    <FunctionName>autoConvertUnicodeCommand</FunctionName>
                  </Action>
                </Control>
                <Control xsi:type="Button" id="TamilToolkit.RepairTextBtn">
                  <Label resid="RepairText.Label" />
                  <Supertip>
                    <Title resid="RepairText.Label" />
                    <Description resid="RepairText.Tooltip" />
                  </Supertip>
                  <Icon>
                    <bt:Image size="16" resid="Icon.Repair.16" />
                    <bt:Image size="32" resid="Icon.Repair.32" />
                    <bt:Image size="80" resid="Icon.Repair.80" />
                  </Icon>
                  <Action xsi:type="ExecuteFunction">
                    <FunctionName>repairTamilCommand</FunctionName>
                  </Action>
                </Control>
                <Control xsi:type="Button" id="TamilToolkit.SortAkaraBtn">
                  <Label resid="SortAkara.Label" />
                  <Supertip>
                    <Title resid="SortAkara.Label" />
                    <Description resid="SortAkara.Tooltip" />
                  </Supertip>
                  <Icon>
                    <bt:Image size="16" resid="Icon.Sort.16" />
                    <bt:Image size="32" resid="Icon.Sort.32" />
                    <bt:Image size="80" resid="Icon.Sort.80" />
                  </Icon>
                  <Action xsi:type="ExecuteFunction">
                    <FunctionName>sortAkaraVarisaiCommand</FunctionName>
                  </Action>
                </Control>
              </Group>

              <Group id="TamilToolkit.ActionsGroup">
                <Label resid="ActionsGroup.Label" />
                <Icon>
                  <bt:Image size="16" resid="Icon.Sel.16" />
                  <bt:Image size="32" resid="Icon.Sel.32" />
                  <bt:Image size="80" resid="Icon.Sel.80" />
                </Icon>
                <Control xsi:type="Menu" id="TamilToolkit.LayoutMenu">
                  <Label resid="LayoutMenu.Label" />
                  <Supertip>
                    <Title resid="LayoutMenu.Label" />
                    <Description resid="LayoutMenu.Tooltip" />
                  </Supertip>
                  <Icon>
                    <bt:Image size="16" resid="Icon.Sel.16" />
                    <bt:Image size="32" resid="Icon.Sel.32" />
                    <bt:Image size="80" resid="Icon.Sel.80" />
                  </Icon>
                  <Items>
                    <Item id="TamilToolkit.HyphenSelItem">
                      <Label resid="HyphenSelection.Label" />
                      <Supertip>
                        <Title resid="HyphenSelection.Label" />
                        <Description resid="HyphenSelection.Tooltip" />
                      </Supertip>
                      <Icon>
                        <bt:Image size="16" resid="Icon.Sel.16" />
                        <bt:Image size="32" resid="Icon.Sel.32" />
                        <bt:Image size="80" resid="Icon.Sel.80" />
                      </Icon>
                      <Action xsi:type="ExecuteFunction">
                        <FunctionName>hyphenateSelectionCommand</FunctionName>
                      </Action>
                    </Item>
                    <Item id="TamilToolkit.HyphenDocItem">
                      <Label resid="HyphenDoc.Label" />
                      <Supertip>
                        <Title resid="HyphenDoc.Label" />
                        <Description resid="HyphenDoc.Tooltip" />
                      </Supertip>
                      <Icon>
                        <bt:Image size="16" resid="Icon.Doc.16" />
                        <bt:Image size="32" resid="Icon.Doc.32" />
                        <bt:Image size="80" resid="Icon.Doc.80" />
                      </Icon>
                      <Action xsi:type="ExecuteFunction">
                        <FunctionName>hyphenateDocumentCommand</FunctionName>
                      </Action>
                    </Item>
                    <Item id="TamilToolkit.WrapNoHyphenItem">
                      <Label resid="WrapNoHyphen.Label" />
                      <Supertip>
                        <Title resid="WrapNoHyphen.Label" />
                        <Description resid="WrapNoHyphen.Tooltip" />
                      </Supertip>
                      <Icon>
                        <bt:Image size="16" resid="Icon.Wrap.16" />
                        <bt:Image size="32" resid="Icon.Wrap.32" />
                        <bt:Image size="80" resid="Icon.Wrap.80" />
                      </Icon>
                      <Action xsi:type="ExecuteFunction">
                        <FunctionName>wrapWithoutHyphenCommand</FunctionName>
                      </Action>
                    </Item>
                    <Item id="TamilToolkit.RemoveHyphensItem">
                      <Label resid="RemoveHyphens.Label" />
                      <Supertip>
                        <Title resid="RemoveHyphens.Label" />
                        <Description resid="RemoveHyphens.Tooltip" />
                      </Supertip>
                      <Icon>
                        <bt:Image size="16" resid="Icon.Del.16" />
                        <bt:Image size="32" resid="Icon.Del.32" />
                        <bt:Image size="80" resid="Icon.Del.80" />
                      </Icon>
                      <Action xsi:type="ExecuteFunction">
                        <FunctionName>removeHyphensCommand</FunctionName>
                      </Action>
                    </Item>
                  </Items>
                </Control>
                <Control xsi:type="Menu" id="TamilToolkit.InsertMenu">
                  <Label resid="InsertMenu.Label" />
                  <Supertip>
                    <Title resid="InsertMenu.Label" />
                    <Description resid="InsertMenu.Tooltip" />
                  </Supertip>
                  <Icon>
                    <bt:Image size="16" resid="Icon.Cal.16" />
                    <bt:Image size="32" resid="Icon.Cal.32" />
                    <bt:Image size="80" resid="Icon.Cal.80" />
                  </Icon>
                  <Items>
                    <Item id="TamilToolkit.InsertDateItem">
                      <Label resid="InsertDate.Label" />
                      <Supertip>
                        <Title resid="InsertDate.Label" />
                        <Description resid="InsertDate.Tooltip" />
                      </Supertip>
                      <Icon>
                        <bt:Image size="16" resid="Icon.Cal.16" />
                        <bt:Image size="32" resid="Icon.Cal.32" />
                        <bt:Image size="80" resid="Icon.Cal.80" />
                      </Icon>
                      <Action xsi:type="ExecuteFunction">
                        <FunctionName>insertTamilDateCommand</FunctionName>
                      </Action>
                    </Item>
                    <Item id="TamilToolkit.NumToWordsItem">
                      <Label resid="NumToWords.Label" />
                      <Supertip>
                        <Title resid="NumToWords.Label" />
                        <Description resid="NumToWords.Tooltip" />
                      </Supertip>
                      <Icon>
                        <bt:Image size="16" resid="Icon.Convert.16" />
                        <bt:Image size="32" resid="Icon.Convert.32" />
                        <bt:Image size="80" resid="Icon.Convert.80" />
                      </Icon>
                      <Action xsi:type="ExecuteFunction">
                        <FunctionName>numberToWordsCommand</FunctionName>
                      </Action>
                    </Item>
                  </Items>
                </Control>
              </Group>
              <Label resid="TabLabel" />
            </CustomTab>
          </ExtensionPoint>
        </DesktopFormFactor>
      </Host>
    </Hosts>
    <Resources>
      <bt:Images>
        <bt:Image id="Icon.16" DefaultValue="${cleanUrl}/assets/icon-16.png?v=${ICON_VER}" />
        <bt:Image id="Icon.32" DefaultValue="${cleanUrl}/assets/icon-32.png?v=${ICON_VER}" />
        <bt:Image id="Icon.80" DefaultValue="${cleanUrl}/assets/icon-80.png?v=${ICON_VER}" />
        <bt:Image id="Icon.Type.16" DefaultValue="${cleanUrl}/assets/type-16.png?v=${ICON_VER}" />
        <bt:Image id="Icon.Type.32" DefaultValue="${cleanUrl}/assets/type-32.png?v=${ICON_VER}" />
        <bt:Image id="Icon.Type.80" DefaultValue="${cleanUrl}/assets/type-80.png?v=${ICON_VER}" />
        <bt:Image id="Icon.Convert.16" DefaultValue="${cleanUrl}/assets/convert-16.png?v=${ICON_VER}" />
        <bt:Image id="Icon.Convert.32" DefaultValue="${cleanUrl}/assets/convert-32.png?v=${ICON_VER}" />
        <bt:Image id="Icon.Convert.80" DefaultValue="${cleanUrl}/assets/convert-80.png?v=${ICON_VER}" />
        <bt:Image id="Icon.Repair.16" DefaultValue="${cleanUrl}/assets/repair-16.png?v=${ICON_VER}" />
        <bt:Image id="Icon.Repair.32" DefaultValue="${cleanUrl}/assets/repair-32.png?v=${ICON_VER}" />
        <bt:Image id="Icon.Repair.80" DefaultValue="${cleanUrl}/assets/repair-80.png?v=${ICON_VER}" />
        <bt:Image id="Icon.Sort.16" DefaultValue="${cleanUrl}/assets/sort-16.png?v=${ICON_VER}" />
        <bt:Image id="Icon.Sort.32" DefaultValue="${cleanUrl}/assets/sort-32.png?v=${ICON_VER}" />
        <bt:Image id="Icon.Sort.80" DefaultValue="${cleanUrl}/assets/sort-80.png?v=${ICON_VER}" />
        <bt:Image id="Icon.Cal.16" DefaultValue="${cleanUrl}/assets/calendar-16.png?v=${ICON_VER}" />
        <bt:Image id="Icon.Cal.32" DefaultValue="${cleanUrl}/assets/calendar-32.png?v=${ICON_VER}" />
        <bt:Image id="Icon.Cal.80" DefaultValue="${cleanUrl}/assets/calendar-80.png?v=${ICON_VER}" />
        <bt:Image id="Icon.Sel.16" DefaultValue="${cleanUrl}/assets/hyphen-sel-16.png?v=${ICON_VER}" />
        <bt:Image id="Icon.Sel.32" DefaultValue="${cleanUrl}/assets/hyphen-sel-32.png?v=${ICON_VER}" />
        <bt:Image id="Icon.Sel.80" DefaultValue="${cleanUrl}/assets/hyphen-sel-80.png?v=${ICON_VER}" />
        <bt:Image id="Icon.Doc.16" DefaultValue="${cleanUrl}/assets/hyphen-doc-16.png?v=${ICON_VER}" />
        <bt:Image id="Icon.Doc.32" DefaultValue="${cleanUrl}/assets/hyphen-doc-32.png?v=${ICON_VER}" />
        <bt:Image id="Icon.Doc.80" DefaultValue="${cleanUrl}/assets/hyphen-doc-80.png?v=${ICON_VER}" />
        <bt:Image id="Icon.Wrap.16" DefaultValue="${cleanUrl}/assets/wrap-nohyphen-16.png?v=${ICON_VER}" />
        <bt:Image id="Icon.Wrap.32" DefaultValue="${cleanUrl}/assets/wrap-nohyphen-32.png?v=${ICON_VER}" />
        <bt:Image id="Icon.Wrap.80" DefaultValue="${cleanUrl}/assets/wrap-nohyphen-80.png?v=${ICON_VER}" />
        <bt:Image id="Icon.Del.16" DefaultValue="${cleanUrl}/assets/remove-hyphen-16.png?v=${ICON_VER}" />
        <bt:Image id="Icon.Del.32" DefaultValue="${cleanUrl}/assets/remove-hyphen-32.png?v=${ICON_VER}" />
        <bt:Image id="Icon.Del.80" DefaultValue="${cleanUrl}/assets/remove-hyphen-80.png?v=${ICON_VER}" />
      </bt:Images>
      <bt:Urls>
        <bt:Url id="Taskpane.Url" DefaultValue="${cleanUrl}/index.html" />
        <bt:Url id="Support.Url" DefaultValue="${cleanUrl}/support.html" />
      </bt:Urls>
      <bt:ShortStrings>
        <bt:String id="GetStarted.Title" DefaultValue="Tamil Toolkit is ready">
          <bt:Override Locale="ta-IN" Value="தமிழ் கருவி தயார்" />
        </bt:String>
        <bt:String id="TabLabel" DefaultValue="தமிழ்" />
        <bt:String id="SuiteGroup.Label" DefaultValue="Tamil Utilities">
          <bt:Override Locale="ta-IN" Value="தமிழ் கருவிகள்" />
        </bt:String>
        <bt:String id="ActionsGroup.Label" DefaultValue="Layout &amp; Insert">
          <bt:Override Locale="ta-IN" Value="அமைப்பு &amp; சேர்" />
        </bt:String>
        <bt:String id="OpenTaskpane.Label" DefaultValue="Tamil Toolkit">
          <bt:Override Locale="ta-IN" Value="தமிழ் கருவி" />
        </bt:String>
        <bt:String id="LiveTyping.Label" DefaultValue="Live Bamini ON/OFF">
          <bt:Override Locale="ta-IN" Value="நேரடி பாமினி" />
        </bt:String>
        <bt:String id="AutoConvert.Label" DefaultValue="Convert to Unicode">
          <bt:Override Locale="ta-IN" Value="Unicode மாற்று" />
        </bt:String>
        <bt:String id="RepairText.Label" DefaultValue="Repair Tamil">
          <bt:Override Locale="ta-IN" Value="எழுத்து சீரமைப்பு" />
        </bt:String>
        <bt:String id="SortAkara.Label" DefaultValue="Sort Akara Varisai">
          <bt:Override Locale="ta-IN" Value="அகரவரிசை" />
        </bt:String>
        <bt:String id="LayoutMenu.Label" DefaultValue="Hyphenation">
          <bt:Override Locale="ta-IN" Value="சொல் பிரிப்பு" />
        </bt:String>
        <bt:String id="InsertMenu.Label" DefaultValue="Insert Tamil">
          <bt:Override Locale="ta-IN" Value="தமிழ் சேர்" />
        </bt:String>
        <bt:String id="HyphenSelection.Label" DefaultValue="Hyphenate Selection">
          <bt:Override Locale="ta-IN" Value="தேர்ந்தெடுத்ததை இணை" />
        </bt:String>
        <bt:String id="HyphenDoc.Label" DefaultValue="Hyphenate Document">
          <bt:Override Locale="ta-IN" Value="முழு ஆவணம் (-)" />
        </bt:String>
        <bt:String id="WrapNoHyphen.Label" DefaultValue="Wrap Without Hyphen">
          <bt:Override Locale="ta-IN" Value="குறியின்றி மடி" />
        </bt:String>
        <bt:String id="RemoveHyphens.Label" DefaultValue="Remove Hyphenation">
          <bt:Override Locale="ta-IN" Value="சொல் பிரிப்பு நீக்கு" />
        </bt:String>
        <bt:String id="InsertDate.Label" DefaultValue="Insert Tamil Date">
          <bt:Override Locale="ta-IN" Value="தமிழ் தேதி சேர்" />
        </bt:String>
        <bt:String id="NumToWords.Label" DefaultValue="Number to Words">
          <bt:Override Locale="ta-IN" Value="எண் → தமிழ் சொல்" />
        </bt:String>
      </bt:ShortStrings>
      <bt:LongStrings>
        <bt:String id="GetStarted.Description" DefaultValue="Open the Tamil tab in the ribbon to convert legacy fonts, repair Unicode, sort Akara Varisai, insert Tamil dates or numerals, and hyphenate." />
        <bt:String id="OpenTaskpane.Tooltip" DefaultValue="Open the Tamil Toolkit utility pane (Type, Prepare, and Insert)." />
        <bt:String id="LiveTyping.Tooltip" DefaultValue="Toggle Live Bamini-to-Unicode typing ON or OFF directly on the Word page." />
        <bt:String id="AutoConvert.Tooltip" DefaultValue="Auto-detect legacy Tamil fonts (Bamini, TSCII, TAB, TAM, Anjal, Vanavil, LT-TM) and convert selection or active paragraph to Unicode." />
        <bt:String id="RepairText.Tooltip" DefaultValue="Normalize to NFC, fix duplicate pullis, and reorder visual vowel signs while preserving ZWJ/ZWNJ." />
        <bt:String id="SortAkara.Tooltip" DefaultValue="Sort selected Tamil paragraphs in authentic Akara Varisai dictionary order (Mei before Uyirmei)." />
        <bt:String id="LayoutMenu.Tooltip" DefaultValue="Canonical Tamil syllabic hyphenation, invisible line wrapping, and hyphen cleanup." />
        <bt:String id="InsertMenu.Tooltip" DefaultValue="Insert today's formatted Tamil solar date or convert a selected number to Tamil words." />
        <bt:String id="HyphenSelection.Tooltip" DefaultValue="Soft-hyphenate the selected text or active paragraph at valid Tamil syllable boundaries." />
        <bt:String id="HyphenDoc.Tooltip" DefaultValue="Soft-hyphenate all body and table paragraphs in the document." />
        <bt:String id="WrapNoHyphen.Tooltip" DefaultValue="Insert zero-width syllable wrap points without showing any visible hyphen." />
        <bt:String id="RemoveHyphens.Tooltip" DefaultValue="Removes only automatic Tamil soft-hyphenation breaks (preserves manual '-' hyphens)." />
        <bt:String id="InsertDate.Tooltip" DefaultValue="Insert today's formatted Tamil solar date and Thiruvalluvar year at the cursor." />
        <bt:String id="NumToWords.Tooltip" DefaultValue="Convert the selected number into formal Tamil words." />
      </bt:LongStrings>
    </Resources>
  </VersionOverrides>
</OfficeApp>
`;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const devXml = renderManifestXml(DEV_BASE_URL);
  const prodXml = renderManifestXml(PROD_BASE_URL);

  fs.writeFileSync(path.join(addinDir, "manifest.xml"), devXml, "utf8");

  if (fs.existsSync(distDir)) {
    fs.writeFileSync(path.join(distDir, "manifest.prod.xml"), prodXml, "utf8");
  }

  console.log(`[build-manifest] Generated manifest.xml (${DEV_BASE_URL}) and dist/manifest.prod.xml (${PROD_BASE_URL})`);
}
