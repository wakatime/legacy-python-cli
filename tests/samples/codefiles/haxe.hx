import alpha.ds.StringMap;
import bravo.macro.*;
import Math.random;
#if js
    js.Browser.alert("Hello");
#elseif sys
    Sys.println("Hello");
#end
import charlie.fromCharCode in f;
import delta.something;
import delta.another.thing;

class Main {
  static public function main() {
    // instead of: new haxe.ds.StringMap();
    new StringMap();
  }
}
