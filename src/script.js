function onload(event) {
  var nodes = document.querySelectorAll("td.inf_name");
  for (var i = 0; i < nodes.length; i++) {
    var node = nodes[i];
    var up = node.parentElement;
    var down = up && up.nextElementSibling;
    if (!down)
      continue;
    if (up.className != "inf_up" || down.className != "inf_down")
      continue;
    var up_height = up.clientHeight;
    var down_height = down.clientHeight;
    if (down_height < up_height)
      node.style.paddingTop = (up_height - down_height) + "px";
  }
};

window.addEventListener("load", onload);
