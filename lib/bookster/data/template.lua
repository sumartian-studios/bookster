-- This script patches include_before, include_body, and include_after to properly handle Markdown files instead of just pasting them as raw files.

local system = require "pandoc.system"
local path = require "pandoc.path"
local text = require "pandoc.text"
local text = require "pandoc.text"


local psvectorian_lookup = {
  -- Miscellaneous Icons (90 - 100)
  ["chicken"]           = 90,
  ["cow"]               = 91,
  ["boot"]              = 92,
  ["wing_top"]          = 93,
  ["quill"]             = 94,
  ["eye"]               = 95,
  ["ear"]               = 96,
  ["nose"]              = 97,
  ["wing_bottom"]       = 98,
  ["scroll_flourish"]   = 99,
  ["flourish_vertical"] = 100,

  -- Figures & Animals (101 - 124)
  ["wings_spread"]      = 101,
  ["scorpion"]          = 102,
  ["archer"]            = 103,
  ["goat"]              = 104,
  ["man_with_leaves"]   = 105,
  ["fish_crossed"]      = 106,
  ["elephant"]          = 107,
  ["horse_running"]     = 108,
  ["mouse"]             = 109,
  ["dog"]               = 110,
  ["boar"]              = 111,
  ["bird_on_branch"]    = 112,
  ["bird_flying"]       = 113,
  ["initial_p"]         = 114,
  ["rose_top"]          = 115,
  ["rose_side"]         = 116,
  ["sunflower"]         = 117,
  ["flower_bud"]        = 118,
  ["man_blowing_horn"]  = 119,
  ["chalice"]           = 120,
  ["spring_coil"]       = 121,
  ["butterfly"]         = 122,
  ["owl"]               = 123,
  ["eagle"]             = 124,

  -- Portraits & Objects (125 - 140)
  ["portrait_man"]      = 125,
  ["pocket_watch"]      = 126,
  ["ship_large"]        = 127,
  ["ship_small"]        = 128,
  ["rings_interlocked"] = 129,
  ["heart"]             = 130,
  ["cherub_left"]       = 131,
  ["cherub_right"]      = 132,
  ["seashell"]          = 133,
  ["lyre"]              = 134,

  -- Objects & Household (167 - 180)
  ["table_stand"]       = 167,
  ["bench_ornate"]      = 168,
  ["frame_empty"]       = 169,
  ["flourish_dynamic"]  = 170,
  ["top_hat"]           = 171,
  ["cap"]               = 172,
  ["harp"]              = 173,
  ["glass_cup"]         = 174,
  ["umbrella"]          = 175,
  ["wheat_bundle"]      = 176,
  ["tulip_vase"]        = 177,
  ["vase_ornate"]       = 178,
  ["pitcher"]           = 179,
  ["jug"]               = 180,

  -- Art & Nature (181 - 196)
  ["stool"]             = 181,
  ["palette"]           = 182,
  ["shell_dish"]        = 183,
  ["cloud_tree"]        = 184,
  ["gate_fence"]        = 185,
  ["infinity_scroll"]   = 186,
  ["horseshoe"]         = 187,
  ["leaf_branch"]       = 188,
  ["floral_tail"]       = 189,
  ["bird_standing"]     = 190,
  ["us_flag"]           = 191,
  ["harp_vertical"]     = 192,
  ["plane_glider"]      = 193,
  ["angel_corner"]      = 194,
  ["angel_flying"]      = 195,
  ["angel_portrait"]    = 196
}

local no_indent_next = false

-- Define the specific transformations for your sub-files
local sub_file_transformations = {
  HorizontalRule = function(el)
    no_indent_next = true
    return pandoc.RawBlock('latex', '\\scenebreak')
  end,

  -- British English suggests no indentation after scenebreak
  Para = function(el)
    if no_indent_next then
      no_indent_next = false
      table.insert(el.content, 1, pandoc.RawInline('latex', '\\noindent '))
      return el
    end
  end
}

-- Automatic dropped capitals
local function automate_lettrine(blocks)
  if not blocks or #blocks == 0 then return blocks end

  local first_content_block = nil
  for i, block in ipairs(blocks) do
    if block.t ~= "Header" then
      first_content_block = block
      break
    end
  end

  if not first_content_block or first_content_block.t ~= "Para" then
    return blocks
  end

  local inlines = first_content_block.content
  if inlines[1] and inlines[1].t == "Str" then
    local content = inlines[1].text
    local first_char = text.sub(content, 1, 1)

    -- See if the first char is NOT a letter
    if first_char:match("^[^%a]") then
      return blocks
    end

    local rest_of_word = text.sub(content, 2)
    inlines[1] = pandoc.RawInline("latex", "\\lettrine{" .. first_char .. "}{" .. rest_of_word .. "}")
  end

  return blocks
end

function HorizontalRule(el)
  return pandoc.RawBlock('latex', '\\scenebreak')
end

-- Parse markdown into Pandoc blocks
local function get_blocks_from_file(path)
  local f = io.open(path, "r")
  if f then
    local content = f:read("*a")
    f:close()

    local doc = pandoc.read(content)
    local filtered_blocks = pandoc.walk_block(pandoc.Div(doc.blocks), sub_file_transformations).content

    return automate_lettrine(filtered_blocks)
  end
  print("Warning: File not found at " .. path)
  return nil
end

function Meta(meta)
  local cli_chapter_dir = meta["chapter-dir"] and pandoc.utils.stringify(meta["chapter-dir"])

  local function process_simple_list(key)
    if meta[key] and type(meta[key]) == "table" then
      local all_blocks = {}
      for _, filename in ipairs(meta[key]) do
        local full_path = pandoc.utils.stringify(filename)
        local blocks = get_blocks_from_file(full_path)
        if blocks then
          for _, b in ipairs(blocks) do table.insert(all_blocks, b) end
        end
      end
      meta[key] = all_blocks
    end
  end

  process_simple_list("include-before")
  process_simple_list("include-after")

  if meta["include-body"] and type(meta["include-body"]) == "table" then
    for _, part in ipairs(meta["include-body"]) do
      if part.ornament ~= nil then
        part.ornament = tostring(psvectorian_lookup[pandoc.utils.stringify(part.ornament)] or 100)
      end

      if part.chapters and type(part.chapters) == "table" then
        local chapter_contents = {}

        local first_val = pandoc.utils.stringify(part.chapters[1])
        local second_val = pandoc.utils.stringify(part.chapters[2])

        if #part.chapters == 2 and tonumber(first_val) and tonumber(second_val) then
          local start_num = tonumber(first_val)
          local end_num = tonumber(second_val)

          local folder = cli_chapter_dir
              or (part.dir and pandoc.utils.stringify(part.dir))
              or "chapters"

          for i = start_num, end_num do
            local blocks = get_blocks_from_file(string.format("%s/chapter-%d.md", folder, i))
            if blocks then
              for _, block in ipairs(blocks) do
                table.insert(chapter_contents, block)
              end
            end
          end
          part.chapters = chapter_contents
        end
      end
    end
  end

  return meta
end
