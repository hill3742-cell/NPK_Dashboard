window.OneSignalDeferred = window.OneSignalDeferred || [];
OneSignalDeferred.push(async function(OneSignal) {
  await OneSignal.init({
    appId: "bf74f838-0208-468e-81a2-0cc2be370b90",
    serviceWorkerParam: { scope: "/" },
    serviceWorkerPath: "/OneSignalSDKWorker.js"
  });
});