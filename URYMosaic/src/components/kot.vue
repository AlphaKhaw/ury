<template>
  <div class="mx-auto p-6 mb-16 relative">
    <!-- Alert Modal div start-->
    <div
      v-if="this.showModal"
      class="fixed inset-0 z-10 overflow-y-auto bg-gray-100"
    >
      <div class="flex items-center justify-center">
        <div class="w-full rounded-lg bg-white p-6 shadow-lg md:max-w-md">
          <p
            class="block text-left text-xl font-medium text-gray dark:text-gray"
          >
            <span
              class="w-3 h-3 rounded-full inline-block mr-1 bg-red-500"
            ></span>
            Not Permitted
          </p>
          <hr class="border-gray-200" />

          <p class="text-left text-xl mt-6 font-medium text-gray-500">
            Log in to access this page.
          </p>

          <div class="flex justify">
            <button
              @click="
                this.showModal = false;
                this.redirectToLogin();
              "
              class="mt-8 rounded bg-blue-500 px-3 py-2 text-white hover:bg-blue-600"
            >
              Login
            </button>
          </div>
        </div>
      </div>
    </div>
    <!-- Alert Modal div end-->

    <div
      class="grid grid-cols-1 gap-10 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
    >
      <div v-for="kot in this.kot" :key="kot.name">
        <div
          :class="[kot.color]"
          class="inline-block shadow-lg gap-4 p-3 rounded-2xl w-90 h-auto masonry-item"
          style="margin-top: 28px"
          v-if="!kot.showDiv && kot.production === production"
        >
          <div class="w-64 check">
            <div
              :class="[{ hidden: !kot.isRotated }]"
              @click="rotateCard(kot)"
              class="absolute inset-0 bg-white z-50 opacity-80 rounded-2xl flex flex-col justify-center items-center"
            >
              <button
                @click="
                  kot.type === 'Cancelled' || kot.type === 'Partially cancelled'
                    ? confirmOrder(kot)
                    : serveOrder(kot)
                "
                :class="[{ hidden: !kot.isRotated }]"
                class="py-2 px-6 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition duration-300 ease-in-out"
              >
                {{
                  kot.type === "Cancelled" || kot.type === "Partially cancelled"
                    ? "Confirm"
                    : "Serve"
                }}
              </button>
            </div>

            
              <!-- Serve Button -->

              <!-- Card Header: Table Name and Order Number -->
              <div class="flex justify-between" @click="rotateCard(kot)">
                <div class="text-sm w-48">
                  <span
                    v-if="kot.tableortakeaway !== 'Takeaway'"
                    class="text-sm font-medium text-[#6B7280]"
                    >Table
                  </span>
                  <span class="text-black-500 font-semibold">
                    {{ kot.tableortakeaway }}
                    <span class="text-sm font-medium text-[#6B7280]"
                      >( {{ kot.user }} )</span
                    ></span
                  ><br />
                  <span v-if="kot.is_aggregator" class="text-sm font-medium text-[#6B7280]">Aggregator</span>
                  <span v-if="kot.is_aggregator" class="text-black-500 ml-2 font-semibold"
                    >{{ kot.customer_name }}
                  </span><br v-if="kot.is_aggregator" />
                  <span v-if="kot.is_aggregator" class="text-sm font-medium text-[#6B7280]">Aggregator ID</span>
                  <span v-if="kot.is_aggregator" class="text-black-500 ml-2 font-semibold"
                    >{{ kot.aggregator_id }}
                  </span><br v-if="kot.is_aggregator"/>
                  <span class="text-sm font-medium text-[#6B7280]">Order</span>
                  <span class="text-black-500 ml-2 font-semibold"
                    >{{ this.daily_order_number ? kot.order_no : kot.invoice.slice(-4) }}
                    
                  </span>
                  <span
                    class="text-black-500 ml-2 font-semibold"
                    v-if="
                      kot.type === 'Partially cancelled' ||
                      kot.type === 'Cancelled'
                    "
                  >
                    ( {{ kot.type }} )</span
                  >
                </div>
                <div
                  :class="kot.timecolor"
                  class="font-inter font-semibold text-2xl leading-10"
                >
                  {{ kot.timeRemaining }}
                </div>
              </div>
              <div
                v-if="kot.type === 'Duplicate'"
                class="text-[#DC0000] font-medium"
              >
                ( Duplicate KOT ( CHECK WITH CAPTAIN ) )
              </div>
              <div v-show="kot.comments" class="text-[#6B7280] font-medium">
                ( {{ kot.comments }} )
              </div>
              <div></div>
              <div>
                <!-- Grouped KOT Items Display -->
                <div v-for="group in getGroupedKotItems(kot)" :key="group.grouping" class="mb-4">
                  <!-- Main Item -->
                  <div
                    @click="
                      () => {
                        toggleItemStrikeThrough(group.mainItem, kot);
                      }
                    "
                    :class="{
                      'line-through text-green-700': group.mainItem.striked,
                    }"
                    class="flex font-semibold justify-between items-center bg-blue-50 p-3 rounded-lg border-l-4 border-blue-500"
                  >
                    <div>
                      <span class="ml-2 text-black-100 font-bold">{{
                        group.mainItem.item_name
                      }}<span v-show="group.mainItem.indicate_course" class="text-sm text-gray-500 ml-1"> ( {{group.mainItem.course}} )</span>
                      </span
                      ><br />
                      <span
                        class="ml-2 text-black-100"
                        v-if="
                          kot.type === 'Partially cancelled' ||
                          kot.type === 'Cancelled'
                        "
                        >[Old Qty = {{ group.mainItem.quantity }}]</span
                      >
                    </div>
                    <div>
                      <span class="ml-2 text-black-100 font-bold">{{ group.mainItem.qty }}</span>
                    </div>
                  </div>
                  
                  <!-- Add-ons for this main item -->
                  <div v-for="addon in group.addons" :key="addon.name" class="ml-6">
                    <div
                      @click="
                        () => {
                          toggleItemStrikeThrough(addon, kot);
                        }
                      "
                      :class="{
                        'line-through text-green-700': addon.striked,
                      }"
                      class="flex font-medium justify-between items-center bg-green-50 p-2 rounded-lg border-l-4 border-green-500"
                    >
                      <div>
                        <span class="ml-2 text-black-100">+ {{
                          addon.item_name
                        }}<span v-show="addon.indicate_course" class="text-sm text-gray-500 ml-1"> ( {{addon.course}} )</span>
                        </span
                        ><br />
                        <span
                          class="ml-2 text-black-100"
                          v-if="
                            kot.type === 'Partially cancelled' ||
                            kot.type === 'Cancelled'
                          "
                          >[Old Qty = {{ addon.quantity }}]</span
                        >
                      </div>
                      <div>
                        <span class="ml-2 text-black-100">{{ addon.qty }}</span>
                      </div>
                    </div>
                    <div>
                      <p
                        v-show="addon.comments"
                        class="ml-8 text-[#6B7280] font-medium text-sm"
                      >
                        {{ addon.comments }}
                      </p>
                    </div>
                  </div>
                  
                  <!-- Main item comments -->
                  <div>
                    <p
                      v-show="group.mainItem.comments"
                      class="ml-2 text-[#6B7280] font-medium"
                    >
                      {{ group.mainItem.comments }}
                    </p>
                    <hr class="my-2 border-gray-200" />
                  </div>
                </div>
              </div>
            
          </div>
          <!-- You can add more item/quantity pairs here as needed -->
        </div>
      </div>
    </div>

    <!-- Audio Alert Message -->
    <div
      v-if="showAudioAlertMessage"
      class="absolute top-1 left-1/2 transform -translate-x-1/2 p-2 font-bold text-2xl text-red-500 text-center"
    >
      Audio notifications disabled. Click anywhere to enable.
    </div>

    <div
      v-if="statusMessage"
      :class="[
        'fixed',
        'bottom-10',
        'right-10',
        'p-4',
        'rounded',
        'text-white',
        {
          'bg-green-500': isOnline,
          'bg-red-500': !isOnline,
        },
      ]"
      @transitionend="handleTransitionEnd"
    >
      {{ statusMessage }}
    </div>
  </div>
</template>

<script>
import { FrappeApp } from "frappe-js-sdk";
import Masonry from "masonry-layout";
import io from "socket.io-client";

let host = window.location.hostname;
let port = window.location.port;
let protocol = window.location.protocol;
let url = port ? `${protocol}//${host}:${port}` : `${protocol}//${host}`;
window.globalSiteName = '';
let socket; 

async function fetchAndSetSiteName() {
    try {
        const response = await fetch('/api/method/ury.ury.api.ury_kot_display.get_site_name', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        const data = await response.json();
        window.globalSiteName = data.message.site_name;
        // console.log('Global Site Name:', window.globalSiteName);
    } catch (error) {
        console.error('Failed to fetch site name:', error);
    }
}

async function initializeSocket() {
    await fetchAndSetSiteName();
    if (window.globalSiteName) {
        let site = window.globalSiteName;
        let site_url = `${url}/${site}`;
        socket = io(site_url,{ withCredentials: true });
        console.log("socket == >",socket)
        socket.on('connect_error', (err) => {
            console.error("Socket connection error:", err);
        }); 
        socket.on('connect', () => {
            console.log('Socket connected:', socket.connected);
        });
    } else {
        console.error('Site name is not set. Socket cannot be initialized.');
    }
}

initializeSocket(); // Initialize the socket after fetching the site name


const frappe = new FrappeApp(url);
export default {
  // inject: ["$auth", "$socket"],
  data() {
    return {
      kot: [],
      masonry: null,
      call: frappe.call(),
      production: "",
      branch: "",
      kot_channel: "",
      clickedItems: new Set(),
      struckThroughItems: {},
      loggeduser: "",
      showModal: false,
      kot_alert_time: "",
      showAudioAlertMessage: false,
      audio_alert: 0,
      isOnline: navigator.onLine,
      statusMessage: "",
      daily_order_number:0
    };
  },
  methods: {
    playAlertSound(path) {
      var currentDomain = window.location.origin;
      var audio_path = currentDomain + path;
      const audio = new Audio(audio_path);
      audio.play();
    },
    auth() {
      return new Promise((resolve, reject) => {
        const auth = frappe.auth();
        auth
          .getLoggedInUser()
          .then((user) => {
            this.loggeduser = user;
            resolve();
          })
          .catch((error) => {
            console.error(error);
            reject(error);
          });
      });
    },
    fetchKOT() {
      return new Promise((resolve, reject) => {
        try {
          this.call
            .get("ury.ury.api.ury_kot_display.kot_list", {})
            .then((result) => {
              console.log(result,"..............result")
              this.branch = result.message.Branch;
              this.kot_alert_time = result.message.kot_alert_time;
              this.audio_alert = result.message.audio_alert;
              this.daily_order_number = result.message.daily_order_number;
              this.kot_channel = `kot_update_${this.branch}_${this.production}`;
              this.kot = result.message.KOT;
              this.updateQtyColorTable();
              this.updateTimeRemaining();
              this.masonryLoading();
              resolve();
            })
            .catch((error) => {
              console.error(error);
              reject(error);
            });
        } catch (error) {
          reject(error);
        }
      });
    },
    rotateCard(kot) {
      this.masonryLoading();
      kot.isRotated = !kot.isRotated;
    },
    confirmOrder(kot) {
      const now = new Date();
      this.currentTime = now.toLocaleTimeString();
      this.call
        .post("ury.ury.api.ury_kot_display.confirm_cancel_kot", {
          name: kot.name,
          user: this.loggeduser,
        })
        .then((result) => {
          // kot.isHidden = !kot.isHidden;
          kot.showDiv = !kot.showDiv;
          // this.showDiv = false;

          this.removeAllItemsFromLocalStorage(kot);
          this.masonryLoading();
        })
        .catch((error) => console.error(error));
    },
    async serveOrder(kot) {
      const now = new Date();
      this.currentTime = now.toLocaleTimeString();

      this.call
        .post("ury.ury.api.ury_kot_display.serve_kot", {
          name: kot.name,
          time: this.currentTime,
        })
        .then((result) => {
          // kot.isHidden = !kot.isHidden;
          kot.showDiv = !kot.showDiv;
          // this.showDiv = false;

          this.removeAllItemsFromLocalStorage(kot);
          this.masonryLoading();
        })
        .catch((error) => console.error(error));
    },

    async orderDelayNotify(kot) {
      const now = new Date();
      this.currentTime = now.toLocaleTimeString();

      this.call
        .post(
          "ury.ury.api.ury_kot_notification.order_delay_notification",
          {
            id: kot.name,
          }
        )
        .then((result) => {
          // console.log("call backed ", result);
        })
        .catch((error) => console.error(error));
    },
    toggleItemStrikeThrough(kotitem, kot) {
      kotitem.striked = !kotitem.striked;
      localStorage.setItem(
        `${kot.name}_${kotitem.name}_strike`,
        JSON.stringify(kotitem.striked)
      );
    },

    updateColorandTable(kot, restaurant_table, type, table_takeaway) {
      if (restaurant_table === undefined) {
        kot.tableortakeaway = "Takeaway";
      } else {
        if (table_takeaway == 1) {
          kot.tableortakeaway = "Takeaway";
        } else {
          kot.tableortakeaway = restaurant_table;
        }
      }
      if (type == "Order Modified") {
        kot.color = "bg-[#FFD493] border border-[#FFC700]";
      } else if (type == "Partially cancelled" || type == "Cancelled") {
        kot.color = "bg-[#FFD2D2] border border-[#FAA7A7]";
      } else if (restaurant_table === undefined || table_takeaway == 1) {
        kot.color = "bg-blue-100 border border-blue-200";
      } else {
        kot.color = "bg-white";
      }
      console.log(type,".............type")
    },
    updateQtyColorTable() {
      this.kot.forEach((kot) => {
        console.log(kot,"kot............")
        this.updateColorandTable(
          kot,
          kot.restaurant_table,
          kot.type,
          kot.table_takeaway
        );

        kot.kot_items.forEach((kotitem) => {
          const savedState = localStorage.getItem(
            `${kot.name}_${kotitem.name}_strike`
          );
          if (savedState) {
            kotitem.striked = JSON.parse(savedState);
          }
          this.calculateQty(
            kotitem,
            kotitem.quantity,
            kot.type,
            kotitem.cancelled_qty
          );
        });
      });
    },
    calculateQty(kotitem, qty, type, cancelled_qty) {
      kotitem.qty = qty;
      if (type == "Partially cancelled" || type == "Cancelled") {
        kotitem.qty = qty - cancelled_qty;
      }
    },
    removeAllItemsFromLocalStorage(kot) {
      // Get all keys in local storage
      const keys = Object.keys(localStorage);
      // Remove keys that start with `${kot.name}_`
      keys.forEach((key) => {
        if (key.startsWith(`${kot.name}_`)) {
          localStorage.removeItem(key);
        }
      });
    },

    updateTimeRemaining() {
      // console.log("update time", this.kot_channel);
      this.kot.forEach((kot) => {
        kot.timeRemaining = this.calculateTimeRemaining(kot.time);

        const timeRemaining = kot.timeRemaining.split(":");
        const minutes =
          parseInt(timeRemaining[0]) * 60 + parseInt(timeRemaining[1]);

        if (
          minutes === this.kot_alert_time &&
          kot.type !== "Cancelled" &&
          kot.type !== "Partially cancelled"
        ) {
          this.orderDelayNotify(kot);
        }
        if (minutes >= this.kot_alert_time) {
          kot.timecolor = "text-[#DC0000]";
        } else {
          kot.timecolor = "text-black";
        }
      });
    },
    calculateTimeRemaining(targetTime) {
      const currentTime = new Date();
      const [targetHours, targetMinutes, targetSeconds] = targetTime.split(":");
      const targetDate = new Date(
        currentTime.getFullYear(),
        currentTime.getMonth(),
        currentTime.getDate(),
        targetHours,
        targetMinutes,
        targetSeconds
      );

      const timeDifference = currentTime - targetDate;
      const hoursRemaining = Math.floor(timeDifference / 3600000);
      const minutesRemaining = Math.floor((timeDifference % 3600000) / 60000);

      return `${hoursRemaining} : ${minutesRemaining}`;
    },
    fetchkotwithmasonry() {
      return this.fetchKOT().then(() => {
        this.masonryLoading();
      });
    },
    redirectToLogin() {
      var currentDomain = window.location.origin;
      window.location.href =
        currentDomain + "/login?redirect-to=URYMosaic/" + this.production;
    },
    masonryLoading() {
      this.$nextTick(() => {
        this.masonry = new Masonry(this.$el.querySelector(".grid"), {
          itemSelector: ".masonry-item",
          gutter: 28,

          // Other Masonry options can be added here
        });
        this.masonry.layout();
      });
    },
    hideAudioAlertMessage() {
      this.showAudioAlertMessage = false;
    },
    handleOnline() {
      this.isOnline = true;
      this.setStatusMessage("You are online");
      this.hideStatusMessageAfterDelay();
      this.fetchKOT().then(() => {
        this.masonryLoading();
      });
    },
    handleOffline() {
      this.isOnline = false;
      this.setStatusMessage("You are Offline");
    },
    setStatusMessage(message) {
      this.statusMessage = message;
    },
    hideStatusMessageAfterDelay() {
      setTimeout(() => {
        this.statusMessage = "";
      }, 3000);
    },
    handleTransitionEnd() {
      if (!this.isOnline) {
        // Reset the status message after transition end
        this.setStatusMessage("");
      }
    },
  },
  mounted() {
    window.addEventListener("online", this.handleOnline);
    window.addEventListener("offline", this.handleOffline);
    document.addEventListener("click", this.hideAudioAlertMessage);
    const currentUrl = window.location.href;
    const parts = currentUrl.split("/");
    const production = parts[parts.length - 1];
    const decodedProduction = decodeURIComponent(production);
    this.production = decodedProduction;
    const self = this;
    window.addEventListener("resize", this.masonryLoading());
    this.masonryLoading();

    this.auth()
      .then(() => {
        self.fetchKOT().then(() => {
          if (this.audio_alert === 1) {
            this.showAudioAlertMessage = true;
          }
          socket.on(this.kot_channel, (doc) => {
            if (this.audio_alert === 1) {
              this.playAlertSound(doc.audio_file);
            }
            let kottime = localStorage.getItem("kot_time");
            if (doc.last_kot_time !== null) {
              if (doc.last_kot_time !== kottime) {
                this.fetchKOT().then(() => {
                  this.masonryLoading();
                });
              }
            }
            this.kot.unshift(doc.kot);
            this.masonryLoading();
            this.updateQtyColorTable();
            this.updateTimeRemaining();
            setTimeout(()=>{
              if (doc.kot.type === "Cancelled"){
                this.fetchKOT().then(() => {
                  this.masonryLoading();
                });
              }
            },1500)
            localStorage.setItem("kot_time", doc.kot.time);
          });
        });
      })
      .catch((error) => {
        console.error("Authentication error:", error);
        this.showModal = true;
      });
    setInterval(this.updateTimeRemaining, 60000);
  },
  beforeDestroy() {
    window.removeEventListener("online", this.handleOnline);
    window.removeEventListener("offline", this.handleOffline);
    document.removeEventListener("click", this.hideAudioAlertMessage);
  },
  computed: {
    sortedKotItems() {
      return (kot) => {
        return kot.kot_items.sort((a, b) => a.serve_priority - b.serve_priority);
      };
    },
    getGroupedKotItems() {
      return (kot) => {
        if (!kot || !kot.kot_items || !Array.isArray(kot.kot_items)) {
          return [];
        }

        const items = kot.kot_items.sort((a, b) => a.serve_priority - b.serve_priority);
        const groups = {};

        // First pass: Create groups for all main items (non-addon items)
        items.forEach(item => {
          if (!item.is_addon) {
            // This is a main item
            // Use item_grouping if available, otherwise create a unique key based on item code
            const groupingKey = item.item_grouping || `main_${item.item}_${item.name}`;

            if (!groups[groupingKey]) {
              groups[groupingKey] = {
                grouping: groupingKey,
                mainItem: item,
                addons: []
              };
            }
          }
        });

        // Second pass: Assign add-ons to their parent groups
        items.forEach(item => {
          if (item.is_addon && item.parent_item) {
            // This is an add-on item, find its parent group
            let foundGroup = false;

            // If item has item_grouping, try to find matching group first
            if (item.item_grouping) {
              if (groups[item.item_grouping]) {
                groups[item.item_grouping].addons.push(item);
                foundGroup = true;
              }
            }

            // If not found by grouping, search for parent by item code
            if (!foundGroup) {
              for (const key in groups) {
                if (groups[key].mainItem && groups[key].mainItem.item === item.parent_item) {
                  groups[key].addons.push(item);
                  foundGroup = true;
                  break;
                }
              }
            }

            // If still not found, create orphaned add-on group
            if (!foundGroup) {
              const orphanKey = `orphan_${item.item}_${item.name}`;
              groups[orphanKey] = {
                grouping: orphanKey,
                mainItem: item,
                addons: []
              };
            }
          }
        });

        // Convert groups object to array and return
        return Object.values(groups);
      };
    },
  },
};
</script>
<style>
.bg-gray-100 {
  background-color: rgba(0, 0, 0, 0.2);
}
</style>
