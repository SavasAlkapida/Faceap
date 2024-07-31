$(document).ready(function() {
    const callClient = new Azure.Communication.Calling.CallClient();
    let callAgent;
    let deviceManager;
    let localVideoStream;
    let call;

    async function getCommunicationToken() {
        const response = await fetch('/get-communication-token/');
        const data = await response.json();
        return data;
    }

    async function initialize() {
        const tokenData = await getCommunicationToken();
        callAgent = await callClient.createCallAgent(tokenData.token);
        deviceManager = await callClient.getDeviceManager();

        await deviceManager.askDevicePermission({ video: true });

        const videoDevices = await deviceManager.getCameras();
        const videoDeviceInfo = videoDevices[0];

        localVideoStream = new Azure.Communication.Calling.LocalVideoStream(videoDeviceInfo);
        const localRenderer = new Azure.Communication.Calling.VideoStreamRenderer(localVideoStream);
        const view = await localRenderer.createView();
        document.getElementById("localVideo").appendChild(view.target);
    }

    initialize();

    $('#startCallButton').on('click', async function() {
        const callOptions = {
            videoOptions: { localVideoStreams: [localVideoStream] }
        };
        const userToCall = prompt("Enter the user ID to call:");
        call = callAgent.startCall([{ communicationUserId: userToCall }], callOptions);

        call.on('remoteParticipantsUpdated', (event) => {
            event.added.forEach(participant => {
                participant.videoStreams.forEach(async (stream) => {
                    const renderer = new Azure.Communication.Calling.VideoStreamRenderer(stream);
                    const view = await renderer.createView();
                    document.getElementById("remoteVideo").appendChild(view.target);
                });
            });
        });
    });

    $('#acceptCallButton').on('click', function() {
        callAgent.on('incomingCall', async (incomingCallEvent) => {
            const incomingCall = incomingCallEvent.incomingCall;
            call = await incomingCall.accept({
                videoOptions: { localVideoStreams: [localVideoStream] }
            });

            call.on('remoteParticipantsUpdated', (event) => {
                event.added.forEach(participant => {
                    participant.videoStreams.forEach(async (stream) => {
                        const renderer = new Azure.Communication.Calling.VideoStreamRenderer(stream);
                        const view = await renderer.createView();
                        document.getElementById("remoteVideo").appendChild(view.target);
                    });
                });
            });
        });
    });

    $('#hangUpButton').on('click', function() {
        if (call) {
            call.hangUp();
        }
    });
});


$(document).ready(function() {
    let selectedCells = [];

    // Hücre seçme ve toplama
    $('td[data-field]').on('click', function() {
        const cell = $(this);
        const cellValue = parseFloat(cell.text()) || 0;

        // Hücre seçimi işlemi
        if (!cell.hasClass('selected')) {
            cell.addClass('selected');
            selectedCells.push(cellValue);
        } else {
            cell.removeClass('selected');
            selectedCells = selectedCells.filter(value => value !== cellValue);
        }

        // Toplam hesaplama
        const sum = selectedCells.reduce((acc, value) => acc + value, 0);
        $('#sum').text(`Toplam: ${sum}`);
    });

    // Hücre güncelleme ve toplamın yeniden hesaplanması
    $('td[contenteditable=true]').on('keydown', function(event) {
        if (event.key === "Enter") {
            event.preventDefault();
            const cell = $(this);
            const adId = cell.data('id');
            const field = cell.data('field');
            const value = parseFloat(cell.text()) || 0;
            const csrfToken = "{{ csrf_token }}";

            $.ajax({
                url: "{% url 'save_advertisements' %}",
                type: "POST",
                data: {
                    csrfmiddlewaretoken: csrfToken,
                    ['ad_' + adId + '_' + field]: value
                },
                success: function(response) {
                    console.log('Saved successfully');
                    // Güncellenen verilerle total_views hesapla ve tabloyu güncelle
                    updateTotalViews(adId);

                    // Seçilen hücreler arasında bu hücre varsa, toplamı yeniden hesapla
                    if (cell.hasClass('selected')) {
                        selectedCells = selectedCells.map(val => val === cellValue ? value : val);
                        const sum = selectedCells.reduce((acc, value) => acc + value, 0);
                        $('#sum').text(`Toplam: ${sum}`);
                    }
                },
                error: function(response) {
                    console.log('Save failed');
                }
            });
        }
    });

    function updateTotalViews(adId) {
        var goruntulemeSayisiFace = parseFloat($('td[data-id="' + adId + '"][data-field="goruntuleme_sayisi_face"]').text()) || 0;
        var goruntulemeSayisiInstgr = parseFloat($('td[data-id="' + adId + '"][data-field="goruntuleme_sayisi_instgr"]').text()) || 0;
        var totalViews = goruntulemeSayisiFace + goruntulemeSayisiInstgr;
        $('td[data-id="' + adId + '"][data-field="total_views"]').text(totalViews);
    }
});
