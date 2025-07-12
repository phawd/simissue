//ajaxSuccess will be called on any object on the page that has added a handler
// like below
//when anyone in the page makes an(y) AJAX request and it results in a success.
//In our case, we want to update the client list whenever a call to
//   /srv/status returns a new value for notificationFlag
$(document).ajaxSuccess(function(e, xhr, settings)
{
	if ((xhr.responseText) && (settings.dataType == "json")) {
		try {
			var obj = jQuery.parseJSON(xhr.responseText || "null");
			if ( typeof obj.statusData.statusBarNotificationFlag !== "undefined") {
				if (obj.statusData.statusBarNotificationFlag === true || obj.statusData.statusBarNotificationFlag > 0) {
					notifications.startPolling();
				} else {
					notifications.stopPolling();
				}
			}
		} catch(e) {
		}
	}
});

var notifications = (function()
{
	var self = {};

	var notificationInterval = null, pollingRate = 2000;

	self.notificationList = [];

	function updateNotificationBar()
	{
		var notificationWrapper = $(".notifications_wrapper.global");
		var notificationCount = self.notificationList.length;


		if (notificationCount > 0) {
			notificationWrapper.empty();
			$.each(self.notificationList, function() {
				var notification = $('<div class="notification global ' + this.severity + '"></div>');
				var notificationInner = $('<div class="notification_inner clearfix"></div>');
				if (typeof this.title !== "undefined") {
					notificationInner.append('<h3 class="title">' + this.title + ': </h3><p class="message aftertitle" id="' + this.id + '">' + this.text + '</p>');
				} else {
					notificationInner.append('<p class="message">' + this.text + '</p>');
				}

				notification.append(notificationInner);

				if ( typeof this.action !== "undefined") {
					var action = $('<a href="' + this.action.href + '">' + this.action.text + '</a>');

					notification.find('p.message').append(action);
				}

				notificationWrapper.append(notification);

			});
			notificationWrapper.show();

			if($("#smsReceived").length > 0) {
                                $("#smsReceived").off("click", "a");
                                $("#smsReceived").on("click", "a", function(e) {
					e.preventDefault();
					var url = $("#smsReceived a").attr("href");
                                        var width, height;
                                        if (isloggedIn == 0) {
                                                smsTitle = loginTitle;
                                                width = 700;
                                                height = "auto";
                                        }
                                        loadHtmlPage(smsTitle, url, width, height);	
				});
			}
		} else {
			notificationWrapper.hide();
		}
	}

	function getNotifications()
	{
		$.ajax({
			url : "/srv/notification",
			type : "GET",
			dataType : "json",
			cache : false,
			success : function(data) {
				if (data.notificationsList) {
					self.notificationList = data.notificationsList;
				} else {
					self.notificationList = [];
				}
				updateNotificationBar();
			},
			error : function(xhr, textStatus, errorThrown) {
				self.notificationList = [];
			},
			complete : function() {
				notificationInterval = setTimeout(getNotifications, pollingRate);
			}
		});
	}


	self.startPolling = function()
	{
		if (notificationInterval == null) {
			getNotifications();
		} else {
			// we don't have to start polling; we are polling already
		}
	};

	self.stopPolling = function()
	{
		window.clearTimeout(notificationInterval);
		notificationInterval = null;
		//notification may be visible for the MiFi unreachable case
		$(".notifications_wrapper.global").hide();
	};

	self.showMiFiUnreachableMessage = function()
	{
		//stop polling
		if (notificationInterval != null) {
			window.clearTimeout(notificationInterval);
			notificationInterval = null;
		}
		if (typeof mifidisconnectlist !== "undefined") self.notificationList = mifidisconnectlist;
		updateNotificationBar();
	};

	return self;
})();

