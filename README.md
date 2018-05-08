# VRcade

What is the VRcade: a real-time location system (RTLS) designed for virtual reality (VR) applications. This system was designed with the intention of tracking the 3D positions of many objects into a virtual coordinate grid, such that the objects tracked can be displayed within the game world.
The motivation for our product was to provide an accurate, scalable, and cost-effective platform for arcade-style VR gaming. Though the current well-established VR technology mainly has functionality for individual consumers and restricts the area of use/locomotion of the player, we believe that it could be as, or more useful, in commercial gaming applications. The idea would be to create a VR system that can function in a large area, with multiple players. This requires a large-scale VR input device, which can determine positions of players and objects within a large play area. To accomplish this goal, the system must be extraordinarily accurate and low latency. Additionally, in order to widely support fledgling businesses that utilize the system, it should be low cost, easy and cheap to install/operate, and be highly scalable and dynamic.

To do this, we created an IR-based RTLS. The system consists of four stationary IR cameras and four mobile "tracker" units, each with four IR LEDs. To allow for multiple trackers, we implemented a timing system to have only one tracker visible to the cameras at once. There is a master camera that sends out an RF pulse to sync each of the other cameras and a tracker for each tracker. The cycle is as follows: the trackers and camera stations receive the sync signal, a tracker activates its LEDs, the cameras all take a picture, and the tracker deactivates its LEDs. The images are then processed to obtain distance information, which is turned into 3D coordinates. This is accomplished through use of perspective projection analysis.

## Authors

* **John Siracusa**
* **Eric Strotman**
* **Mark Lust**
* **Jacob Kruzer**
* **Samuel Taylor**

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
