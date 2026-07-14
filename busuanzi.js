/* 站点访问统计(不蒜子)—— 低调挂在页脚,显示总访问量 / 访客数。
   用法:在页脚备案脚本(beian.js)之后加一行 <script src="./busuanzi.js"></script>
   (栏目内页面用 ../busuanzi.js,404 兜底页用 /busuanzi.js)。
   数据由不蒜子提供,拿到数字前整行隐藏,不占位、不闪动。 */
(function () {
  // 统计行:未取到数字前用 display:none 藏起来(不蒜子会把容器显出来)。
  document.currentScript.insertAdjacentHTML('beforebegin',
    '<p style="text-align:center;font-size:.72rem;color:#B4A896;margin:2px 0 0;letter-spacing:.02em;">' +
      '<span id="busuanzi_container_site_uv" style="display:none;">' +
        '👀 <span id="busuanzi_value_site_uv"></span> 位小朋友来过' +
      '</span>' +
      '<span id="busuanzi_container_site_pv" style="display:none;">' +
        '&nbsp;·&nbsp;共翻开 <span id="busuanzi_value_site_pv"></span> 次' +
      '</span>' +
    '</p>');

  // 异步加载不蒜子,不阻塞页面。
  var s = document.createElement('script');
  s.async = true;
  s.src = '//busuanzi.ibruce.info/busuanzi/2.3/busuanzi.pure.mini.js';
  document.head.appendChild(s);
})();
