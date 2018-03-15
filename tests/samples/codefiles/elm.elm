module Index exposing (..) -- where

import Color exposing (Color, darkGrey)
import Dict
import TempFontAwesome as FA
import Html exposing (..)
import Html.Attributes exposing (..)
import Markdown
import String


-- MAIN


main =
  Html.programWithFlags
    { init = init
    , view = view
    , update = update
    , subscriptions = subscriptions
    }
