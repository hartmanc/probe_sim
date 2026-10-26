# AI engine families: CC BY rebuild ledger (26 Oct 2026, branch `audio-ccby`)

Owner's decision (26 Oct 2026): every shipped family loop comes from CC BY audio, the owner's own footage, or
synthesis. The four mixed families were re-cut from their CC BY sources only, the six with no clean source got CC BY
replacements, and the synthesiser was written and checked but **not needed**: all six searches turned something up.
`mazda_kl_v6` (the Probe's own set) is untouched, and so are `bmw_m20_i6`, `mazda_b_i4` and `subaru_fa20_flat4`
(already all CC BY; their engine.json was not rebuilt).

Every licence below was read from the video's own page with `yt-dlp -J` (`license` field: "Creative Commons Attribution
license (reuse allowed)" = CC BY 3.0) before the audio was downloaded; `fetch_audio.py` refuses anything else. All 32
original sources were re-checked the same way on 26 Oct 2026: the 12 CC BY and 20 Standard YouTube License split in the
owner's inventory is exactly right.

## Before / after

| Family | Outcome | Before: sources (CC BY / Standard) | Before real bins on/off | After: sources (all CC BY) | After real bins on/off | Bins |
|---|---|---|---|---|---|---|
| `bmw_m20_i6` | unchanged (already clean) | 3 (3 / 0) | 23/13 of 23 | 3 videos (all CC BY) | 23/13 of 23 | 1000-6500 step 250 |
| `classic_v8_lowrev` | replaced | 3 (0 / 3) | 11/14 of 18 | 4 videos (all CC BY) | 15/10 of 18 | 750-5000 step 250 |
| `gm_sbc_v8` | replaced | 3 (0 / 3) | 19/16 of 21 | 7 videos (all CC BY) | 21/19 of 21 | 1000-6000 step 250 |
| `mazda_b_i4` | unchanged (already clean) | 2 (2 / 0) | 21/16 of 26 | 2 videos (all CC BY) | 21/16 of 26 | 1000-7250 step 250 |
| `mini_supercharged_i4` | re-cut | 2 (1 / 1) | 22/20 of 24 | 1 videos (all CC BY) | 20/17 of 24 | 1000-6750 step 250 |
| `modern_i4_stock` | replaced | 1 (0 / 1) | 21/15 of 24 | 10 videos (all CC BY) | 23/24 of 24 | 1000-6750 step 250 |
| `ohv_v6` | replaced | 5 (0 / 5) | 20/13 of 21 | 5 videos (all CC BY) | 18/16 of 21 | 1000-6000 step 250 |
| `sohc_i4_loud` | re-cut | 3 (2 / 1) | 23/21 of 23 | 1 videos (all CC BY) | 23/19 of 23 | 1000-6500 step 250 |
| `subaru_fa20_flat4` | unchanged (already clean) | 2 (2 / 0) | 27/21 of 27 | 2 videos (all CC BY) | 27/21 of 27 | 1000-7500 step 250 |
| `toyota_1jz_turbo` | re-cut | 2 (1 / 1) | 25/23 of 25 | 1 videos (all CC BY) | 22/18 of 25 | 1000-7000 step 250 |
| `twincam_i4_loud` | re-cut + added sources | 2 (1 / 1) | 12/13 of 14 | 9 videos (all CC BY) | 13/12 of 14 | 1000-7500 step 500 |
| `vintage_i6` | replaced | 2 (0 / 2) | 16/9 of 18 | 6 videos (all CC BY) | 14/12 of 18 | 750-5000 step 250 |
| `vw_aircooled_flat4` | replaced | 2 (0 / 2) | 16/13 of 16 | 8 videos (all CC BY) | 16/12 of 16 | 1000-4750 step 250 |

Sources per family after the rebuild (channel, title, upload date, url):

**`bmw_m20_i6`**
- Condor Speed Shop - CONSPDSHP - In-car footage in our BMW E30 325i at Sebring International Raceway (20190124) https://www.youtube.com/watch?v=6WRPJvR2WS4 [0-600 s] 
- Xavier FotoFilms - Albert Naval - 45a Pujada Sant Feliu de Codines 2017 | ONBORD | BMW E30 325i (20180123) https://www.youtube.com/watch?v=HUAyMS1s-2o [30-205 s] 
- Heup Motorsport - Heup Motorsport BMW E30 325 Gr  A Mike Heup Trackday Hockenheimring Pistenclub (20200131) https://www.youtube.com/watch?v=dWwXwV9anu4 [3-147 s] 

**`classic_v8_lowrev`**
- Old Skool Only - It Drives! - V8 Model A Pickup build Pt 35 (20230825) https://www.youtube.com/watch?v=HcHmKAwgcyM [0-579 s] Old / lazy V8 (Buick Roadmaster, Ford flathead and Model A pickups) at low to mid rpm; the Roadmaster autocross run supplies the upper bins; supplies 5 real bins
- Artist Group - 1940 Ford truck drive (20120807) https://www.youtube.com/watch?v=wz5KhVihj9w [0-185 s] Old / lazy V8 (Buick Roadmaster, Ford flathead and Model A pickups) at low to mid rpm; the Roadmaster autocross run supplies the upper bins; supplies 1 real bins
- RJK Photographs - RJ Takes the Buick Roadmaster Wagon to Autocross! (20210520) https://www.youtube.com/watch?v=SNOKBHvGkMM [0-585 s] Old / lazy V8 (Buick Roadmaster, Ford flathead and Model A pickups) at low to mid rpm; the Roadmaster autocross run supplies the upper bins; supplies 18 real bins
- jettapup - Test Drive randy's shop truck, 54 Ford  Pick'Em up. (20190217) https://www.youtube.com/watch?v=wNmK7ktrYt8 [0-273 s] Old / lazy V8 (Buick Roadmaster, Ford flathead and Model A pickups) at low to mid rpm; the Roadmaster autocross run supplies the upper bins; supplies 1 real bins

**`gm_sbc_v8`**
- Mechanikas Lukas - Pralėkim su Chevrolet Corvette 1975m 5.7l "SmallBlock" V8 (20190604) https://www.youtube.com/watch?v=AnrfN2Y4Ujc [0-401 s] Small-block Chevy (Corvette / Camaro / Nova / Trans-Am) race and drive footage with a V8 ladder; supplies 4 real bins
- Flemings Ultimate Garage - American Classic 1978 Corvette  - Details, Test Drive and Revs (20220319) https://www.youtube.com/watch?v=q0bKH47di3A [0-489 s] Small-block Chevy (Corvette / Camaro / Nova / Trans-Am) race and drive footage with a V8 ladder; supplies 1 real bins
- Drew Z - 1985 Camaro at Sugar River Raceway Autocross 2011 (20110621) https://www.youtube.com/watch?v=qvuo-WjkXTM [0-166 s] Small-block Chevy (Corvette / Camaro / Nova / Trans-Am) race and drive footage with a V8 ladder; supplies 6 real bins
- Ant Frank - CHEVY CAMARO Z28 DYNO PULLS!!! CANT BELIEVE IT!!! (20200127) https://www.youtube.com/watch?v=x_vvWQNAg64 [0-600 s] Small-block Chevy (Corvette / Camaro / Nova / Trans-Am) race and drive footage with a V8 ladder; supplies 8 real bins
- SVRAlife - 1970 Trans Am Race at Watkins Glen International (20220908) https://www.youtube.com/watch?v=3nMGllH92Lo [0-600 s] Small-block Chevy (Corvette / Camaro / Nova / Trans-Am) race and drive footage with a V8 ladder; supplies 15 real bins
- MicrophonicFool - 1986 Firebird-Drive Through Trenton Ontario (20150303) https://www.youtube.com/watch?v=4eO7RcGtuwU [0-600 s] Small-block Chevy (Corvette / Camaro / Nova / Trans-Am) race and drive footage with a V8 ladder; supplies 1 real bins
- DREAMGOATINC - 1966 Chevrolet ChevY II SS Nova Race Car w Track Action (20260111) https://www.youtube.com/watch?v=hfeQlkpWpaE [0-199 s] Small-block Chevy (Corvette / Camaro / Nova / Trans-Am) race and drive footage with a V8 ladder; supplies 5 real bins

**`mazda_b_i4`**
- Eastern Racing - Mid-Ohio w/Chicane - 97 Miata - 1:48 lap (20170604) https://www.youtube.com/watch?v=K5DDUCfYHGo [0-294 s] 
- the stiglette - Big Willow Spec Miata Race Lap Record! | NASA SoCal Willow Springs (20240418) https://www.youtube.com/watch?v=3Fv5YkvPM80 [0-95 s] 

**`mini_supercharged_i4`**
- Xendar - Autodromo di Franciacorta - 09/06/2011 - MINI Cooper S (R53) (20110613) https://www.youtube.com/watch?v=SBlZ5kUf6c0 [90-900 s] R53 Mini Cooper S Tritec with the supercharger whine, Franciacorta track session; supplies 37 real bins

**`modern_i4_stock`**
- Joe Black - 2005 Ford Fiesta ST (2.0 I 150HP) | POV Test Drive #719 Joe Black (20210326) https://www.youtube.com/watch?v=GXPpsN8j_F8 [0-399 s] Stock-exhaust small four (Duratec / Beta / D-series / GA-series class) on road and track footage with clear pulls to high rpm; supplies 3 real bins
- mad monkey - 2005 Ford Fiesta ST | 2.0 I 150HP | POV Test Drive (20210325) https://www.youtube.com/watch?v=eks1sd4zdD4 [0-347 s] Stock-exhaust small four (Duratec / Beta / D-series / GA-series class) on road and track footage with clear pulls to high rpm; supplies 1 real bins
- Joe Black - 2000 Hyundai Accent II [1.3 i 12V 75HP] |0-100| POV Test Drive #1633 Joe Black (20230401) https://www.youtube.com/watch?v=CJ0xuPqcFxw [0-661 s] Stock-exhaust small four (Duratec / Beta / D-series / GA-series class) on road and track footage with clear pulls to high rpm; supplies 4 real bins
- mad monkey - 1997 Honda Civic |1.4 i 75 HP| POV Test Drive (20211001) https://www.youtube.com/watch?v=IxagQjs0Atg [0-395 s] Stock-exhaust small four (Duratec / Beta / D-series / GA-series class) on road and track footage with clear pulls to high rpm; supplies 8 real bins
- Joe Black - 2006 Suzuki Swift [1.3 92HP] |0-100| POV Test Drive #1920 Joe Black (20231228) https://www.youtube.com/watch?v=ONuffRtHI8o [0-700 s] Stock-exhaust small four (Duratec / Beta / D-series / GA-series class) on road and track footage with clear pulls to high rpm; supplies 1 real bins
- Max Briscoe - Honda Civic EF Hatchback POV Drive (Pure Sound) (20240415) https://www.youtube.com/watch?v=rXQUyg5KRwM [0-568 s] Stock-exhaust small four (Duratec / Beta / D-series / GA-series class) on road and track footage with clear pulls to high rpm; supplies 18 real bins
- Pasión B13 - Nissan tsuru TRACK DAY| Nissan sentra b13, chevrolet optra, peugeot 106, nissan  (20191030) https://www.youtube.com/watch?v=7iv7nvukIQo [0-700 s] Stock-exhaust small four (Duratec / Beta / D-series / GA-series class) on road and track footage with clear pulls to high rpm; supplies 5 real bins
- Ezoy - Toyota Corolla E11 G6 onboard Race track Autodrom Pomorze (20190901) https://www.youtube.com/watch?v=eXjzEcFTFS8 [0-254 s] Stock-exhaust small four (Duratec / Beta / D-series / GA-series class) on road and track footage with clear pulls to high rpm; supplies 4 real bins
- Adhara Racing - Adhara Racing | Mazda 3 Track Time Salinas Copa Liberty 3/22/15 (20150329) https://www.youtube.com/watch?v=IKWxL1COu-U [0-254 s] Stock-exhaust small four (Duratec / Beta / D-series / GA-series class) on road and track footage with clear pulls to high rpm; supplies 1 real bins
- Pasión B13 - Así se siente mi Nissan Sentra b13/ Tsuru en CARRETERA, GoPro POV, Test drive Ts (20210121) https://www.youtube.com/watch?v=NDh81sR5_Yg [0-587 s] Stock-exhaust small four (Duratec / Beta / D-series / GA-series class) on road and track footage with clear pulls to high rpm; supplies 2 real bins

**`ohv_v6`**
- Late Night Auto Mods - 2001 Mustang V6 Custom Flowmaster Exhaust - Revving and Driving (20190817) https://www.youtube.com/watch?v=yaqBp5UYiYw [0-63 s] Pushrod 60-degree V6 (Ford 3.8 Essex in a Mustang, GM 2.8 / 3800 in Fieros and Buick, with their even-fire V6 ladder); the best match to the Vulcan / GM 60-degree class found under CC BY; supplies 12 real bins
- Strong Speed Works - Fiero "GTP" 3800 SUPERCHARGED 5 SPEED! What GM should’ve done! (20250413) https://www.youtube.com/watch?v=zGmxkrmyL2A [0-500 s] Pushrod 60-degree V6 (Ford 3.8 Essex in a Mustang, GM 2.8 / 3800 in Fieros and Buick, with their even-fire V6 ladder); the best match to the Vulcan / GM 60-degree class found under CC BY; supplies 8 real bins
- Luciano's Classics - 1988 Pontiac Fiero GT – V6 Engine and Exhaust Sound (20261014) https://www.youtube.com/watch?v=_gEqUYRBjsw [0-86 s] Pushrod 60-degree V6 (Ford 3.8 Essex in a Mustang, GM 2.8 / 3800 in Fieros and Buick, with their even-fire V6 ladder); the best match to the Vulcan / GM 60-degree class found under CC BY; supplies 2 real bins
- Warfighter Racing - 13.5 Second Quarter Mile Stock 3.8 (20190323) https://www.youtube.com/watch?v=8A_nihfQRx8 [0-232 s] Pushrod 60-degree V6 (Ford 3.8 Essex in a Mustang, GM 2.8 / 3800 in Fieros and Buick, with their even-fire V6 ladder); the best match to the Vulcan / GM 60-degree class found under CC BY; supplies 2 real bins
- Jason Bowman Loves Cars - Pontiac Fiero (20211027) https://www.youtube.com/watch?v=DD_O71Kol70 [0-500 s] Pushrod 60-degree V6 (Ford 3.8 Essex in a Mustang, GM 2.8 / 3800 in Fieros and Buick, with their even-fire V6 ladder); the best match to the Vulcan / GM 60-degree class found under CC BY; supplies 9 real bins

**`sohc_i4_loud`**
- Sixer Fotografia - Rally Crono Ciudad de Jerez 2013 Onboard VW Golf mk2 gti 8v (20131113) https://www.youtube.com/watch?v=kWF6wrCWZqc [15-360 s] VW Golf Mk2 GTI 8v (SOHC-class loud four) rally stage onboard, two stretches of the same CC BY stage; supplies 21 real bins
- Sixer Fotografia - Rally Crono Ciudad de Jerez 2013 Onboard VW Golf mk2 gti 8v (20131113) https://www.youtube.com/watch?v=kWF6wrCWZqc [380-900 s] VW Golf Mk2 GTI 8v (SOHC-class loud four) rally stage onboard, two stretches of the same CC BY stage; supplies 21 real bins

**`subaru_fa20_flat4`**
- Tor C. Anderson - 20190406 Thunderhill West Stock BRZ (20190412) https://www.youtube.com/watch?v=ulfEijjU_uo [3-271 s] 
- Tor C. Anderson - 20190525 Sonoma Stock BRZ (20190527) https://www.youtube.com/watch?v=frfVmzom6I8 [7-157 s] 

**`toyota_1jz_turbo`**
- Auto Factory REALIZE - Auto Factory Realize S13 1JZ RAW Onboard (20181214) https://www.youtube.com/watch?v=EogETCaowYw [10-425 s] 1JZ-GTE swapped S13 onboard (Auto Factory Realize), the only CC BY source with the turbo straight six; supplies 40 real bins

**`twincam_i4_loud`**
- iLLWiLLeM - 20v AE86 around ButtonWillow GOODSOUND (20140128) https://www.youtube.com/watch?v=hEbxnRiE_8w [0-197 s] High-revving DOHC fours: Toyota 4A-GE (AE86 touge, hillclimb, rally and 20v sound clips) and Honda B18 / K20 (Civic, Integra) on track; supplies 2 real bins
- Supreme Tsekereke - Insane Touge Gunsai Skills (AE86 Onboard) (20170511) https://www.youtube.com/watch?v=x6RR_b5qdy0 [0-286 s] High-revving DOHC fours: Toyota 4A-GE (AE86 touge, hillclimb, rally and 20v sound clips) and Honda B18 / K20 (Civic, Integra) on track; supplies 2 real bins
- Supreme Tsekereke - Insane Touge Skills ( AE 86 - ONBOARD ) (20160603) https://www.youtube.com/watch?v=PXYXbdFS4Ak [0-326 s] High-revving DOHC fours: Toyota 4A-GE (AE86 touge, hillclimb, rally and 20v sound clips) and Honda B18 / K20 (Civic, Integra) on track; supplies 1 real bins
- Supreme Tsekereke - Crazy hillclimb AE86 onboard (20170201) https://www.youtube.com/watch?v=uua_uxt4U0c [0-189 s] High-revving DOHC fours: Toyota 4A-GE (AE86 touge, hillclimb, rally and 20v sound clips) and Honda B18 / K20 (Civic, Integra) on track; supplies 1 real bins
- Supreme Tsekereke - Madman Drifting AE86 onboard (20170628) https://www.youtube.com/watch?v=s-xkEtgMI34 [0-171 s] High-revving DOHC fours: Toyota 4A-GE (AE86 touge, hillclimb, rally and 20v sound clips) and Honda B18 / K20 (Civic, Integra) on track; supplies 8 real bins
- Mats vd Brand - #Grabfeldrallye 2018 Toyota Corolla AE86 by #MatsvdBrand & #HeinVerschuuren (20180708) https://www.youtube.com/watch?v=UAIOgJ-FoTc [0-255 s] High-revving DOHC fours: Toyota 4A-GE (AE86 touge, hillclimb, rally and 20v sound clips) and Honda B18 / K20 (Civic, Integra) on track; supplies 1 real bins
- Throttlebuddies - Toyota 4AGE 20V Silver Top | Sounds in the Mountains, RAW 8000 RPM (20240128) https://www.youtube.com/watch?v=iYgb96pqtnI [0-162 s] High-revving DOHC fours: Toyota 4A-GE (AE86 touge, hillclimb, rally and 20v sound clips) and Honda B18 / K20 (Civic, Integra) on track; supplies 4 real bins
- P. E. (Patrick Evers) - Honda Civic EK K20 Nurburgring Nordschleife POV BTG (20200518) https://www.youtube.com/watch?v=_HKDHl5iTM4 [0-400 s] High-revving DOHC fours: Toyota 4A-GE (AE86 touge, hillclimb, rally and 20v sound clips) and Honda B18 / K20 (Civic, Integra) on track; supplies 3 real bins
- DNT DATA NINE TECHNOLOGY - Honda Integra DC2 Type R Monster Hill Climb Racing (20190509) https://www.youtube.com/watch?v=qMP1QbgKboc [0-195 s] High-revving DOHC fours: Toyota 4A-GE (AE86 touge, hillclimb, rally and 20v sound clips) and Honda B18 / K20 (Civic, Integra) on track; supplies 3 real bins

**`vintage_i6`**
- MicrophonicFool - 1966 Valiant-Outside Camera Drive (20190805) https://www.youtube.com/watch?v=jb6ybAkOSS4 [0-500 s] Slow-revving pushrod inline sixes: Plymouth Valiant slant six, Hudson Hornet 308, Jeep 4.0 (road and track footage up to ~5000 rpm); supplies 6 real bins
- 53hornet - Hudson Hornet - First Drive (20141007) https://www.youtube.com/watch?v=UI6zXwCgMmE [0-105 s] Slow-revving pushrod inline sixes: Plymouth Valiant slant six, Hudson Hornet 308, Jeep 4.0 (road and track footage up to ~5000 rpm); supplies 2 real bins
- Joe Black - 1993 Jeep Wrangler I | POV Test Drive #586 Joe Black (20200806) https://www.youtube.com/watch?v=53RNi-6aJjw [0-291 s] Slow-revving pushrod inline sixes: Plymouth Valiant slant six, Hudson Hornet 308, Jeep 4.0 (road and track footage up to ~5000 rpm); supplies 5 real bins
- 53hornet - Drive Your Hudson Day 2025 (20260302) https://www.youtube.com/watch?v=4ZQcJCxacvA [0-500 s] Slow-revving pushrod inline sixes: Plymouth Valiant slant six, Hudson Hornet 308, Jeep 4.0 (road and track footage up to ~5000 rpm); supplies 1 real bins
- Joe Black - 1999 Jeep Grand Cherokee [4.0 i 190HP] |0-100| POV Test Drive #1755 Joe Black (20230710) https://www.youtube.com/watch?v=FLv66j3l_hE [0-500 s] Slow-revving pushrod inline sixes: Plymouth Valiant slant six, Hudson Hornet 308, Jeep 4.0 (road and track footage up to ~5000 rpm); supplies 6 real bins
- mad monkey - 1999 Jeep Grand Cherokee | 4.0 i 190HP | POV Test Drive (20230805) https://www.youtube.com/watch?v=zd0aKsTzgKU [0-405 s] Slow-revving pushrod inline sixes: Plymouth Valiant slant six, Hudson Hornet 308, Jeep 4.0 (road and track footage up to ~5000 rpm); supplies 6 real bins

**`vw_aircooled_flat4`**
- VINTAGE SPEED - Vintage Speed Super Beetle on TRACK 麗寶賽車場 車主日 (20190520) https://www.youtube.com/watch?v=vZVC7jzXOqw [0-143 s] Air-cooled VW Type 1 flat four on track, street and dyno footage (Vintage Speed Super Beetle / 4-2-1 exhaust, trackday and drive clips); supplies 10 real bins
- Gill Pecceu - VW Type 1 Aircooled (20110619) https://www.youtube.com/watch?v=D-NseyssD-c [0-307 s] Air-cooled VW Type 1 flat four on track, street and dyno footage (Vintage Speed Super Beetle / 4-2-1 exhaust, trackday and drive clips); supplies 2 real bins
- vwexotic - VW Type 1 Aircooled (20120624) https://www.youtube.com/watch?v=52pmvXHqnog [0-307 s] Air-cooled VW Type 1 flat four on track, street and dyno footage (Vintage Speed Super Beetle / 4-2-1 exhaust, trackday and drive clips); supplies 1 real bins
- VINTAGE SPEED - Vintage Speed Maximum Speed 4 into 2 into 1 Exhaust vw Type 4 German Look Bug (20200918) https://www.youtube.com/watch?v=u9gp704Yj1Y [0-238 s] Air-cooled VW Type 1 flat four on track, street and dyno footage (Vintage Speed Super Beetle / 4-2-1 exhaust, trackday and drive clips); supplies 10 real bins
- VINTAGE SPEED - Vintage Speed German Look Road and Track VW bug SS143 Exhaust (20190619) https://www.youtube.com/watch?v=6Xzi2JWTRxY [0-81 s] Air-cooled VW Type 1 flat four on track, street and dyno footage (Vintage Speed Super Beetle / 4-2-1 exhaust, trackday and drive clips); supplies 1 real bins
- ntt420 - Old 1978 Red VW California Convertible Vintage Beetle Bug, Driving in Portland O (20111126) https://www.youtube.com/watch?v=jpHBZsKvawI [0-429 s] Air-cooled VW Type 1 flat four on track, street and dyno footage (Vintage Speed Super Beetle / 4-2-1 exhaust, trackday and drive clips); supplies 2 real bins
- Paweł VW Pasja - Vw typ1 1303 convertible on the dyno chasis 1915ccm (20120526) https://www.youtube.com/watch?v=4QslHYR7jm4 [0-46 s] Air-cooled VW Type 1 flat four on track, street and dyno footage (Vintage Speed Super Beetle / 4-2-1 exhaust, trackday and drive clips); supplies 1 real bins
- Pimento Momento - Volkswagen Beetle country drive - GoPro looking back out the OVAL WINDOW (20160421) https://www.youtube.com/watch?v=fRy32FIE8rY [0-500 s] Air-cooled VW Type 1 flat four on track, street and dyno footage (Vintage Speed Super Beetle / 4-2-1 exhaust, trackday and drive clips); supplies 1 real bins


Notes on the bins column: `real` = cut from a recording at its own rpm; the rest are pitch-shifted from the nearest real
bin of the same load (as before). Fewer real bins in `toyota_1jz_turbo`, `sohc_i4_loud` (off), `mini_supercharged_i4`
and `ohv_v6` (on) is the direct cost of dropping the Standard-licence clips; `modern_i4_stock` and `gm_sbc_v8` got more, and
`twincam_i4_loud` is level (13/12 against 12/13) but now rests on nine sources instead of two. `index.json` is unchanged except each family's `real_bins` count.

## Dropped (Standard YouTube License, no longer in any source list)

`sohc_i4_loud`: Pat driving #411 Volvo 240 (BNE) - `toyota_1jz_turbo`: Mark Reijne onboard at Zandvoort 2012 (Kees Reijne) -
`mini_supercharged_i4`: Supercharged R53 Mini, Nurburgring GP (Headrest mount) - `twincam_i4_loud`: JDM AE86 4AG Tsukuba
(runningfree86) - `modern_i4_stock`: Nurburgring Mazda 3 (Chemiekeule) - `classic_v8_lowrev`: 1936 Ford V8 Sunday Drive, 1936
Ford Flathead Road Trip (AutoEsoterica), Dodge Charger 318 (Andre Carrillo - AV8), the skipped flathead clip (Y-Block Guy) -
`gm_sbc_v8`: Symphony of Horsepower 68 Camaro (AutoXandTrack), Nasty 350 V8 (AlwinSV), '69 Camaro (Big Rig Racing) -
`ohv_v6`: Lemons Ranger (Randy Wolfgram), Taurus open header (cjo1979), Probe LX (joe sischo), Ranger WOT and Aerostar
(Intechdude300) - `vintage_i6`: Polara slant six (Yoryi), 1954 Corvette POV (@911r), the skipped Hudson Lemons chase
(Bret Dodson) - `vw_aircooled_flat4`: 1967 Beetle Lignieres (TheSaemi), Super Beetle autocross (Travis B).

## What was searched (step 2)

- **Method:** YouTube search with the Creative Commons filter (`sp=EgIwAQ%253D%253D`) through yt-dlp's search-URL
  extractor, 135 queries over the six families (flathead / Y-block / 318 / Olds / big old V8s; small-block Chevy race
  cars, Camaros, Corvettes, Novas, Trans-Am; modern stock fours by make; Vulcan, 3800, 4.3, 2.8, Mustang 3.8 V6s; 1950s-60s
  and Jeep / AMC / Valiant sixes; air-cooled VW racing, dyno, Baja, Ghia; 4A-GE / K20 / B18 / Alfa twin-cams).
  About 1,900 distinct video ids came back; roughly 80 were checked on their own page (licence, channel, date, duration)
  and 64 had their audio fetched and run through the tracker. The search filter is not proof, so every accepted source
  was checked again on its own page.
- **Accepted** means the tracker found a usable ladder (median comb contrast, share of frames above 2 dB) and the
  source supplied at least one real bin after the candidate scoring. Sources that supplied none were marked `skip` in
  `sources.json` (url kept, audio deleted) and are not in engine.json or credits.json.
- **Quality bar** is the existing one (rpm-bin coverage, seam correlation, A-weighted level matching; README / NOTES.md),
  plus one new guard (below).

## New guard: order ladder (octave check)

`build_family.py` now rejects a candidate loop whose strongest engine order (0.5-step orders up to 12, +-4 % windows) is
not on a whole multiple of the firing order (cylinders / 2); for V8s only a half order is rejected (a cross-plane V8
may lead with order 1 or 2). An octave-slipped label peaks at F/2. On the old modern_i4_stock draft it removed four
suspect top-rpm bins (6500 and 6750, both loads). `qa_orders.py FAMILY` runs the same test on the shipped sprites: every
rebuilt family passes 100 % of its real bins (modern_i4_stock 47/47, gm_sbc_v8 40/40, classic_v8_lowrev 25/25, vintage_i6
26/26, ohv_v6 34/34, vw_aircooled_flat4 28/28, twincam_i4_loud 25/25, toyota 40/40, sohc 42/42, mini 37/37).
It cannot catch a whole source being an octave out in a way that still sits on the ladder (see "Weak spots").

## Synthesis (step 3): written, validated, not shipped

`tools/audio/families/synth_engine.py` is the procedural generator (firing events at the crank angles with per-event
amplitude and timing jitter, Gaussian blow-down pulses through quarter-wave exhaust modes and a tail-pipe low-pass,
intake-stroke noise bursts through a Helmholtz-like band-pass, valve-train ticks, a load-dependent block-noise floor, all
built on the loop's own FFT grid so each loop is exactly periodic). It writes the same sprites / engine.json through
`write_family` with `sources: [{"src": "synth", ...}]` and tier `synth`. Because every one of the six families found CC BY
audio, **no family ships synthesised**. I ran it end to end on `vw_aircooled_flat4` and restored the real build
(`git checkout`), and fitted profiles for `vintage_i6`, `ohv_v6` and `vw_aircooled_flat4` as the likely fallbacks
(`synth_eq.json`). Spectrum match against a clean real family at the same rpm (mean |dB| of the 1/3-octave
harmonic envelope, 63 Hz - 5 kHz, three rpm points x on / off; the harmonic-to-floor contrast in dB, synth vs real):

| Synth family | Reference | Envelope match | Harmonic-to-floor contrast |
|---|---|---|---|
| vintage_i6 | bmw_m20_i6 (clean I6) | 5.8 dB | 39.0 vs 39.2 |
| ohv_v6 | the Probe's own KL-DE V6 | 5.3 dB | 41.2 vs 41.4 |
| vw_aircooled_flat4 | subaru_fa20_flat4 (clean boxer) | 5.6 dB | 44.2 vs 39.0 (too tonal) |

The residual 5-6 dB is mostly individual harmonic levels (a real note has uneven harmonics); the fixed-in-Hz EQ that
closes the bulk of the gap (from 8-11 dB) was fitted against the reference once and stored, the generator never reads
the reference. I have not heard it; treat it as a fallback to be judged by ear before it replaces any real family.

## Listen test (step 7): there is no ear here

I cannot listen to audio in this environment, so the "play each on sprite at idle, mid and redline" step was replaced by
`tools/audio/families/listen_check.py`, which decodes each family's **AAC fallback** sprites and measures the on-throttle
loop at the idle, mid and redline bins: level, peak, spectral centroid, share below 300 Hz, strongest engine order and the
firing-ladder share of the harmonic power, the loop-seam step (jump across the seam over the 95th percentile of the
loop's own sample steps), and the off-throttle gap. **Someone with ears still needs to play them** (`?track=` race with
the field on, or the fallback sprites directly); the numbers below say the loops are on the right ladder and not clipped,
nothing about taste.

| Family | rpm (tier) | RMS dB | peak dB | centroid Hz | <300 Hz | top order | firing-ladder share | seam step | off-on dB |
|---|---|---|---|---|---|---|---|---|---|
| bmw_m20_i6 | 1000 (sweep) | -15.4 | -8.1 | 219 | 96% | 12 | 61% | 0.5 | 5.5 |
| bmw_m20_i6 | 3750 (steady) | -21.6 | -13.1 | 512 | 54% | 4.5 | 16% | 0.3 | 1.0 |
| bmw_m20_i6 | 6500 (sweep) | -20.5 | -10.3 | 414 | 52% | 1.5 | 39% | 0.6 | -3.4 |
| classic_v8_lowrev | 750 (sweep) | -14.1 | -5.3 | 189 | 90% | 10 | 7% | 1.0 | -12.8 |
| classic_v8_lowrev | 2750 (steady) | -20.4 | -7.7 | 501 | 22% | 8 | 68% | 0.3 | 2.5 |
| classic_v8_lowrev | 4750 (pitch-shifted) | -18.2 | -8.3 | 313 | 33% | 4 | 48% | 0.4 | 1.0 |
| gm_sbc_v8 | 1000 (steady) | -7.5 | -0.9 | 78 | 99% | 4 | 96% | 0.1 | -20.9 |
| gm_sbc_v8 | 3500 (steady) | -23.3 | -13.8 | 534 | 14% | 8 | 67% | 1.5 | -5.7 |
| gm_sbc_v8 | 6000 (sweep) | -22.9 | -12.7 | 520 | 23% | 4 | 55% | 0.7 | -5.9 |
| mazda_b_i4 | 1000 (pitch-shifted) | -20.9 | -10.0 | 668 | 64% | 8 | 93% | 0.0 | -0.4 |
| mazda_b_i4 | 4000 (pitch-shifted) | -18.0 | -5.2 | 720 | 78% | 2 | 88% | 0.9 | -5.1 |
| mazda_b_i4 | 7250 (sweep) | -18.0 | -8.4 | 321 | 71% | 2 | 66% | 0.5 | -6.1 |
| mini_supercharged_i4 | 1000 (pitch-shifted) | -16.9 | -6.7 | 263 | 66% | 8 | 71% | 1.6 | 6.2 |
| mini_supercharged_i4 | 3750 (steady) | -20.3 | -9.1 | 513 | 55% | 4 | 81% | 0.5 | 1.2 |
| mini_supercharged_i4 | 6750 (sweep) | -16.6 | -7.8 | 272 | 89% | 2 | 93% | 0.1 | -3.7 |
| modern_i4_stock | 1000 (steady) | -11.9 | -5.2 | 151 | 97% | 8 | 94% | 0.7 | -1.0 |
| modern_i4_stock | 3750 (steady) | -13.5 | -5.5 | 170 | 85% | 2 | 98% | 1.5 | -0.0 |
| modern_i4_stock | 6750 (pitch-shifted) | -22.0 | -12.1 | 949 | 37% | 2 | 60% | 0.1 | -4.9 |
| ohv_v6 | 1000 (sweep) | -24.0 | -14.9 | 265 | 55% | 9 | 77% | 2.1 | 19.3 |
| ohv_v6 | 3500 (steady) | -22.5 | -14.1 | 234 | 88% | 3 | 84% | 1.9 | -1.7 |
| ohv_v6 | 5750 (sweep) | -29.1 | -17.3 | 805 | 37% | 3 | 70% | 0.1 | -4.3 |
| sohc_i4_loud | 1000 (steady) | -19.3 | -10.0 | 433 | 48% | 8 | 90% | 0.3 | -0.4 |
| sohc_i4_loud | 3750 (steady) | -16.1 | -8.4 | 254 | 83% | 2 | 90% | 0.1 | -5.3 |
| sohc_i4_loud | 6500 (sweep) | -17.1 | -9.0 | 322 | 86% | 2 | 88% | 0.8 | -3.5 |
| subaru_fa20_flat4 | 1000 (sweep) | -14.3 | -4.4 | 210 | 96% | 8 | 73% | 1.1 | -6.4 |
| subaru_fa20_flat4 | 4250 (sweep) | -22.4 | -10.6 | 758 | 34% | 2 | 54% | 0.3 | -8.0 |
| subaru_fa20_flat4 | 7500 (sweep) | -14.0 | -6.5 | 199 | 92% | 1 | 33% | 0.4 | -5.3 |
| toyota_1jz_turbo | 1000 (steady) | -17.8 | -8.6 | 330 | 30% | 9 | 82% | 0.4 | 1.6 |
| toyota_1jz_turbo | 4000 (pitch-shifted) | -13.7 | -7.6 | 210 | 97% | 3 | 98% | 0.8 | -3.5 |
| toyota_1jz_turbo | 7000 (sweep) | -20.3 | -10.9 | 485 | 11% | 3 | 57% | 1.9 | -1.9 |
| twincam_i4_loud | 1000 (pitch-shifted) | -10.4 | -5.4 | 150 | 98% | 8 | 99% | 1.1 | -5.4 |
| twincam_i4_loud | 4000 (steady) | -23.7 | -11.4 | 1145 | 9% | 8 | 85% | 1.0 | -4.1 |
| twincam_i4_loud | 7500 (steady) | -16.5 | -8.5 | 285 | 91% | 2 | 91% | 1.8 | -9.9 |
| vintage_i6 | 750 (steady) | -9.7 | -0.6 | 86 | 98% | 6 | 73% | 3.4 | 1.5 |
| vintage_i6 | 2750 (steady) | -12.2 | -5.2 | 131 | 99% | 3 | 97% | 4.8 | -2.0 |
| vintage_i6 | 4750 (pitch-shifted) | -9.6 | -1.5 | 104 | 99% | 3 | 51% | 8.3 | -11.8 |
| vw_aircooled_flat4 | 1000 (steady) | -19.0 | -12.3 | 283 | 67% | 8 | 99% | 1.3 | 11.7 |
| vw_aircooled_flat4 | 2750 (steady) | -13.9 | -5.3 | 172 | 97% | 4 | 95% | 4.9 | -14.2 |
| vw_aircooled_flat4 | 4500 (steady) | -14.6 | -5.7 | 160 | 92% | 2 | 66% | 0.9 | -12.5 |


Reading the table: every on loop peaks under 0 dBFS (highest -0.6 dB; the idle bins of `vintage_i6` and `gm_sbc_v8` are
bass-heavy, 98-99 % of their power under 300 Hz). For the rebuilt inline, flat and V6 families the firing-order ladder
carries most of the harmonic power (51-99 %); the unchanged clean `bmw_m20_i6` and `subaru_fa20_flat4` have a few lower
bins (16-39 %) and the V8 families lead with orders 4 and 8 as a V8 should (`classic_v8_lowrev` idle is 7 %: its
750 rpm loop is a lumpy low burble). Of the 39 loops measured, 35 have a seam step of 3 or less; the four above are
`vintage_i6` at 750 (3.4), 2750 (4.8) and 4750 (8.3, pitch-shifted) and `vw_aircooled_flat4` at 2750 (4.9), all
low-frequency-heavy loops where the 95th-percentile step is tiny. A scan of every bin of four families put the clean
references at up to 2.7-3.4 and `vintage_i6` / `vw_aircooled_flat4` at up to 8.5 / 6.4, so those two are the ones to
listen to for a thump once per loop; the cause is the codec step the README describes, which the player's
`healLoopSeams` smooths. I did not re-listen for a click.

## Weak spots to listen for first

1. **Octave of whole sources.** The comb tracker cannot tell rpm from rpm/2 on a weak source, and the per-source octave
   rule decided most of the rebuilt families. The order guard removed the clear cases, but a source that is consistently an
   octave out still sits on the ladder. Candidates to hear first: `gm_sbc_v8` (the 1970 Trans Am Watkins Glen clip tracked
   at only 1000-3900 rpm, which is low for a race V8, and the Camaro dyno clip was relabelled x2 and reaches 7500) and
   `twincam_i4_loud` (the 20v AE86 clip flipped between x1 and x2 depending on the window). Fix, if wrong: an `octave` pin
   on that entry in `sources.json` and a rebuild (tracks are cached, a minute).
2. **V8 confidence is low.** `classic_v8_lowrev` and `gm_sbc_v8` sources reach only 1-42 % of frames above 2 dB comb
   contrast (old exhausts and wind). `classic_v8_lowrev` leans on one source (the Buick Roadmaster autocross run) for 18
   real bins; above ~3900 rpm it is pitch-shifted from there.
3. **Level and tone of the new top bins.** `modern_i4_stock` now uses a dozen unrelated road cars from 1.3 to 2.0 L;
   neighbouring bins can change character. `ohv_v6` bins 1200-2800 come from one 63-second Mustang 3.8 clip with a
   Flowmaster, so it will sound louder and rougher than a stock Vulcan.
4. `twincam_i4_loud` stays at 500 rpm bins (the 200 KB budget gives 0.4 s loops at 250 rpm steps).

## Tooling added / changed (all under `tools/audio/`, force-added: the folder is in `.git/info/exclude`)

`families/fetch_audio.py` (licence-checked audio-only download into a fresh dir, FLAC mono 48 kHz), `set_sources.py`,
`finalize_sources.py` (per-source "why", skip the unused), `usage.py`, `qa_orders.py`, `make_credits.py`, `listen_check.py`,
`synth_engine.py` + `synth_eq.json`, `test_licences.py`. `build_family.py`: octave guard, `write_family()` shared with the
synthesiser, the listening sweep goes to `cache/` and **no `preview.mp3` is written**, `channel` and `upload_date` in
engine.json sources, `--js-runtimes node` for yt-dlp. `make_index.py --real-bins-only` updates only `real_bins`.

## Tests

- `python3 -I -m pytest tools/audio/test_licences.py` (via `uv run --with pytest`): every `sources[]` entry in every
  `engine.json` is CC BY, the owner's own footage, or synth; credits.json has exactly those urls; no `preview.mp3`;
  the engine.json schema keys and sample rate are unchanged.
- `src/app/__tests__/audio-families-assign.test.ts` (vitest): `familyFor` over the three field identity files
  (45 + 104 + 136 cars) equals a baseline taken on `main` 6f890b9, `index.json`'s family ids / aliases / fallback / default /
  per-car rows are identical, and every family's engine.json, both sprites, the AAC fallback files and bin offsets exist.
  The baseline was written before any file was changed.

## Credits data

`public/audio/families/credits.json`, schema `{"families": {"<id>": [{"title","channel","url","licence"}]}}`, one row per
distinct video (60 rows over 14 families; `mazda_kl_v6` is the owner's own footage with an empty url). The licence string
is the one YouTube shows. Rebuild with `python3 -I tools/audio/families/make_credits.py`.

## Machine notes

Disk was 11-14 GB free throughout; the audio cache stayed under 1.7 GB and was emptied to 80 MB (json records and rpm
tracks) at the end, FLACs are re-fetched from the url on a rebuild. Battery never under 56 %. One heavy process at a time.


# Round two: quality gates (26 Oct 2026, branch `audio-quality` from `release-040`)

The owner listened to round one's clips and wrote: `mazda_kl_v6` "OK"; `sohc_i4_loud` "OK"; `modern_i4_stock` "Weird
speech at 0:03 / High revs / upshift sounds like an organ note at 0:05"; `classic_v8_lowrev` "Doesn't sound correct.
0:01 sounds like a VHS tape rewinding. Sounds loopy, dropping revs sound squeaky". Nobody here can listen, so his words
became measurable gates, the families were rebuilt against them, and the clips were rendered again for his ear.

## The measurement (`families/quality.py`, `families/speechcheck.py`)

Decodes each family's shipped Ogg sprites as Chrome does, heals the seams as `audio.ts` does, and measures every bin
and load: **speech** (the Silero VAD over the loop tiled to 3 s; webrtcvad, the engine-cycle residual's voice-band level
and spectral flux are reported too, but webrtcvad calls 97-100 % of every engine loop speech, so it cannot decide);
**pitch ratio** from the real recording the loop came from; **idle playback** (the family idle played on the lowest
bin); **loop length** and engine cycles; **loopiness** (envelope autocorrelation at the loop period); **seam**
correlation and step; **ladder share** (tonality); **A-weighted level**; sprite **bytes**.

Speech rule: Silero in at least 8 % of the 32 ms windows. Calibrated on round one's loops: clean engine loops reach at
most 5 %; a synthetic voice (macOS `say`) mixed into `sohc_i4_loud` / `modern_i4_stock` loops at -6 dB reaches 78-92 %
(median), at 0 dB 97-100 %. The build rejects at 3 % (so a pitch-shifted copy cannot cross the gate) and also runs Silero
over every whole source, so a candidate overlapping a voice (+-0.3 s) is never cut.

Gates (`test_quality.py`): no speech in any family; every bin within x0.88-1.14 (on) / x0.85-1.18 (off) of a real
recording; the lowest bin a real idle recording that plays the family idle inside those windows; every loop >= 1.0 s
and >= 8 engine cycles; family median seam correlation not below round one's (`quality_baseline.json`); Ogg + json
<= 650 KB. `mazda_kl_v6` and `sohc_i4_loud` are held to the speech gate only (the owner's ear; both pass it).

## His notes, traced

- **"Weird speech at 0:03"** (`modern_i4_stock`): a real voice. The clip reaches 4250 rpm at 3.8 s of the first-gear
  climb; that on-throttle loop was cut from the Nissan B13 track-day video (src6 @ 56.9 s). Silero hears speech in 100 %
  of the loop and, on the source itself, 0.96 mean probability over 55-59.5 s. Across all 14 families round one had
  speech in 42 loops: `ohv_v6` 13, `vw_aircooled_flat4` 10, `vintage_i6` 6, `gm_sbc_v8` 6, `subaru_fa20_flat4` 4,
  `modern_i4_stock`, `classic_v8_lowrev` and `twincam_i4_loud` 1 each (narrated reviews and in-car voices); none in the
  owner's two. After: 0 in every family.
- **"Organ note" on the upshift at 0:05** (`modern_i4_stock`). (a) The clip: a linear 0.25 s glide from the redline to
  62 % with the load crossfading to the off layer; round one's off loops at 4000-5750 rpm were strongly tonal (ladder
  share 0.75-0.97, the spectral gate leaves almost no noise between harmonics), so the glide is a clean harmonic tone
  sliding in pitch. (b) The game: `tools/audio/shift_trace.ts` runs the physics (car #38 built as the race builds it,
  #41 and the Probe) at full throttle. The torque cut lasts 0.15 s, then the automatic clutch re-engages with the
  throttle back on, the driven wheels spin up and the slip dies away: 59-74 % of the rpm drop happens with throttleOut = 1,
  and 90 % of it takes 0.42-0.77 s. `audio-field.ts` follows the physics rpm within 8 ms, so in the game the loaded
  on-layer glides for half a second, longer than in the clip. The game does it too. Fixed on the game side (below).
- **"VHS tape rewinding" at 0:01** (`classic_v8_lowrev`): the idle. 650 rpm was played on the 750 bin, a sweep loop
  recorded at 748 rpm (x0.87), with no real idle anywhere in the family; every family's idle was pitched (x0.35-0.87).
- **"Dropping revs sound squeaky"**: the off-throttle loops above 3750 rpm were one recording pitched up x1.06-1.33.
- **"Loopy"**: round one's `classic_v8_lowrev` loops were 0.24-0.68 s (median 0.61): a lumpy V8 burble repeating
  1.5-4 times a second. Every family's loops were 0.36-0.85 s.

## Before / after (quality.py on the shipped sprites)

| Family | when | real on/off | speech loops | ratio fails (min-max) | real idle in gate | loop median s (fails) | seam corr median | Ogg + json |
|---|---|---|---|---|---|---|---|---|
| `modern_i4_stock` | before | 23/24 | 1 | 0 (0.99-1.04) | no | 0.48 (48) | 0.90 | 182 KB |
| | after | 25/17 | 0 | 0 (0.91-1.17) | yes | 1.12 (0) | 0.85 | 385 KB |
| `sohc_i4_loud` | before | 23/19 | 0 | 1 (0.80-1.04) | no | 0.48 (46) | 0.83 | 183 KB |
| | after | 23/19 | 0 | 1 (0.80-1.04) | no | 0.48 (46) | 0.83 | 183 KB |
| `classic_v8_lowrev` | before | 15/10 | 1 | 3 (0.86-1.33) | no | 0.61 (36) | 0.72 | 168 KB |
| | after | 17/6 | 0 | 0 (0.87-1.11) | yes | 1.12 (0) | 0.63 | 313 KB |
| `vintage_i6` | before | 14/12 | 6 | 1 (0.75-1.08) | no | 0.65 (36) | 0.84 | 157 KB |
| | after | 10/2 | 0 | 6 (0.85-2.07) | yes | 1.13 (0) | 0.87 | 310 KB |
| `mazda_b_i4` | before | 21/16 | 0 | 7 (0.45-1.14) | no | 0.42 (52) | 0.73 | 189 KB |
| | after | 25/10 | 0 | 2 (0.85-1.16) | no | 1.12 (0) | 0.82 | 435 KB |
| `bmw_m20_i6` | before | 23/13 | 0 | 3 (0.50-1.09) | no | 0.48 (46) | 0.71 | 172 KB |
| | after | 25/12 | 0 | 0 (0.86-1.13) | yes | 1.13 (0) | 0.81 | 387 KB |
| `gm_sbc_v8` | before | 21/19 | 6 | 0 (0.96-1.05) | no | 0.54 (42) | 0.68 | 161 KB |
| | after | 23/20 | 0 | 1 (0.88-1.14) | yes | 1.13 (0) | 0.61 | 357 KB |
| `twincam_i4_loud` | before | 13/12 | 1 | 2 (0.66-1.01) | no | 0.60 (28) | 0.73 | 145 KB |
| | after | 29/23 | 0 | 0 (0.97-1.14) | yes | 1.12 (0) | 0.72 | 465 KB |
| `ohv_v6` | before | 18/16 | 13 | 1 (0.81-1.13) | no | 0.52 (42) | 0.84 | 174 KB |
| | after | 19/5 | 0 | 3 (0.70-1.14) | no | 1.13 (0) | 0.84 | 367 KB |
| `toyota_1jz_turbo` | before | 22/18 | 0 | 2 (0.57-1.08) | no | 0.43 (50) | 0.82 | 167 KB |
| | after | 26/13 | 0 | 0 (0.91-1.17) | yes | 1.13 (0) | 0.87 | 406 KB |
| `subaru_fa20_flat4` | before | 27/21 | 4 | 2 (0.67-1.14) | no | 0.40 (54) | 0.61 | 174 KB |
| | after | 29/19 | 0 | 0 (0.86-1.14) | yes | 1.12 (0) | 0.70 | 436 KB |
| `vw_aircooled_flat4` | before | 16/12 | 10 | 2 (0.57-1.00) | no | 0.72 (32) | 0.75 | 154 KB |
| | after | 16/4 | 0 | 0 (1.00-1.17) | yes | 1.13 (0) | 0.76 | 260 KB |
| `mini_supercharged_i4` | before | 20/17 | 0 | 7 (0.44-1.00) | no | 0.48 (48) | 0.78 | 180 KB |
| | after | 25/15 | 0 | 0 (0.89-1.01) | no | 1.10 (0) | 0.68 | 394 KB |
| `mazda_kl_v6` | before | 20/20 | 0 | 2 (0.66-1.13) | no | 0.85 (45) | 0.65 | 335 KB |
| | after | 20/20 | 0 | 2 (0.66-1.13) | no | 0.85 (45) | 0.65 | 335 KB |


Not in the table: loopiness (envelope repeat salience) stays 0.6-0.85 median in every family before and after (it
measures how distinct one repeat is, not how often it comes); what changed is the rate: a 1.1 s loop repeats 0.9 times
a second instead of 2-4. Sprite size roughly doubled (Ogg + json 145-190 KB to 260-470 KB per family; the AAC fallback
pair is about 2x the Ogg); a race loads only the families on the grid.

**Tests** (`uv run --with pytest,numpy,scipy,soundfile,webrtcvad-wheels,onnxruntime python -I -m pytest
tools/audio/test_quality.py tools/audio/test_licences.py`): on round one's audio (`QUALITY_PUBLIC` = release-040's
public/audio) **42 failed, 35 passed**; on round two **12 failed, 69 passed** (licence gate 4/4 passed). The 12:
pitch ratio `vintage_i6`, `mazda_b_i4`, `gm_sbc_v8`, `ohv_v6`; real idle `mazda_b_i4`, `ohv_v6`,
`mini_supercharged_i4`; seam median `modern_i4_stock` (0.85 vs 0.90), `classic_v8_lowrev` (0.63 vs 0.72), `gm_sbc_v8`
(0.61 vs 0.68), `twincam_i4_loud` (0.72 vs 0.73), `mini_supercharged_i4` (0.68 vs 0.78). No gate was loosened.

## What changed in the build (`build_family.py`)

- Loops >= max(1.0 s, 8 engine cycles), up to 1.5 s. Where no single steady stretch is that long, **two or three real
  stretches at the same rpm are joined** (`chain_loop`): each a whole number of cycles, each head crossfaded with what
  follows the previous segment in its own recording, start points chosen for the weakest join, segments within 6 dB of
  each other's 1/3-octave envelope. Tier stays steady / sweep / idle (all real); `source` names every part.
- **Idle bin**: the full-range tracker reads a quiet idle 2-6x too high, so idle has its own track over 0.6-2.2 x the
  family idle (confident, steady, in the source's quieter half, no speech). The idle bin sits at the recording's own rpm
  inside the gate window and serves both loads (tier `idle`). The grid below 1000 rpm is in 125 rpm steps (no two bins
  more than x1.25 apart); near idle (<= 2 x idle) an unloaded steady stretch can serve a bin for both loads.
- **Fill rule**: a missing bin is pitch-shifted only from a real loop of the same load within the window, else it is
  the other load's real loop at that rpm (an on loop is darkened for the overrun: tier `from-on`), else the nearest
  (reported as a gate failure). Every filled copy is speech-checked; a voice-like copy makes the next option be tried.
- **V8s are tracked at double speed**: their half-order ladder at 650-2000 rpm is 5-17 Hz apart, inside the tracker's
  170 ms window resolution, so the comb contrast was ~0.1 dB on every old-V8 source (0-23 % of frames > 2 dB). At x2
  the median rises to 1-3 dB (12-79 % of frames), and the idle reads where the cycle autocorrelation puts it.
- Speech: Silero over every source (cached `cache/speech_*.npz`), rejection at 3 % per candidate loop.
- Start-up / rev clips get `octave: 1.0` in `sources.json` (the per-source median rule assumes driving footage).
- The seam weighs double in the candidate score (8 x rho).

## Sources added (87, all CC BY: licence read from each video's page by `fetch_audio.py` before the audio-only download)

**`classic_v8_lowrev`** (17)
- Aaron Starnes - Driving a 1949 Ford Flathead with Three on the Tree (20190611) https://www.youtube.com/watch?v=pZXO6CXJH3Q
- Erwin Lindsen - Ford Model A 3.6 V8 1929 Hotrod Exhaust Sound (20160127) https://www.youtube.com/watch?v=JZMyQQ23FzI [octave pinned x1]
- Erwin Lindsen - Dodge Panel Delivery Van 5.2 V8 Ratlook 1947 Sound and Driving away (20160124) https://www.youtube.com/watch?v=EkOh-ScdSCk
- Clay Benson - 1954 Cadillac Series 62 Coupe Start and Drive (20111212) https://www.youtube.com/watch?v=2BUGK30gZJs
- Erwin Lindsen - Ford 2 Door Saloon 1937 Hot Rod V8 Exhaust Sound (20170130) https://www.youtube.com/watch?v=R-O0YFaofaY [octave pinned x1]
- Mirko Lorenz - Ford V8 289 CI Engine: Testrun (20120403) https://www.youtube.com/watch?v=eqbbKYs8P3Y
- Mustang Bob - Engine Surge 289 V8 (20181006) https://www.youtube.com/watch?v=N6eG2-oHC6Y
- MicrophonicFool - 1951 Mercury Starts and Smells (20190428) https://www.youtube.com/watch?v=Dzq3sYlYqdg
- Buddy Huggins - 1950 Ford Flathead V8 Engine 3 Speed For Sale near Rogersville MO (20170824) https://www.youtube.com/watch?v=TfiPg_VH-sA
- Classic Muscle Cars - 68 MUSTANG FASTBACK  : Dyno, Cold Start, & Acceleration (20201224) https://www.youtube.com/watch?v=4mNaAH76kVE
- Erwin Lindsen - Ford Pickup Hot Rod 1935 Sound (20120409) https://www.youtube.com/watch?v=j0KQWKYqmKs [octave pinned x1]
- BigBarkozSpeedShop - BBSS - 1961 Buick LeSabre Cold Start (20200415) https://www.youtube.com/watch?v=Lm1FTfIo9kA [octave pinned x1]
- Erik Lundgren - Ardun Equipped Ford Flathead V8 - #57 Ford Special (20140121) https://www.youtube.com/watch?v=Ce7rHmN7kEU
- JohnOdahl - Ford 1932 v8 roadster on dyno (20190709) https://www.youtube.com/watch?v=0EQArgz_vt4
- Js Antiguidades - MOTOR V8 FORD FLATHEAD 8BA (20161101) https://www.youtube.com/watch?v=l0flubp4CKI [octave pinned x1]
- bevmushroomhead - 67 Oldsmobile Cutlass 430 big block buick test run (20120513) https://www.youtube.com/watch?v=af6bAtKnc2o
- Parley Banz - Ford flathead V8 starting up after 10 years of sitting (20141228) https://www.youtube.com/watch?v=r7oief2WVew [octave pinned x1]

**`vintage_i6`** (9)
- Burnitzki Cars & More - 1964 Plymouth Valiant 225 Slant Six Cold Start (20181225) https://www.youtube.com/watch?v=GtmyEycIJ_w [octave pinned x1]
- MicrophonicFool - 1966 Valiant Custom 200 Engine Start (20150703) https://www.youtube.com/watch?v=NwhDaWYbl1g [octave pinned x1]
- 53hornet - Revving a Hudson 308 Big Six - Now This Is Just Fooling Around (20161218) https://www.youtube.com/watch?v=_1T2XLeRStg [octave pinned x1]
- 53hornet - Hudson Hornet First Start! (20141007) https://www.youtube.com/watch?v=aLf3KejsISA [octave pinned x1]
- Erwin Lindsen - Jeep Cherokee 4.0i Acceleration, Exhaust Sound & Revs (20160822) https://www.youtube.com/watch?v=0BsZzuX1SLs [octave pinned x1]
- Erwin Lindsen - Jeep Cherokee 4.0i Exhaust Sound & Revs (20160505) https://www.youtube.com/watch?v=07NO6_8Yrp8 [octave pinned x1]
- Luciano's Classics - Text 1992 Jeep Wrangler Islander 4.0 HO Walkaround, Startup and Sound (short version) (20260223) https://www.youtube.com/watch?v=CaSqMZcMEEs [octave pinned x1]
- Jacob Neal - 1993 Ford F150 4x4 5spd 4.9L L6 300 Straight Six Walkaround (20131120) https://www.youtube.com/watch?v=wznw1qMkx60 [octave pinned x1]
- Luciano's Classics - 1988 Jeep Wrangler Laredo Walkaround, Startup and Sound (short version) (20250419) https://www.youtube.com/watch?v=rrXg781iefo [octave pinned x1]

**`mazda_b_i4`** (9)
- Ride in Japan - MAZDA MX5 Miata 1.6L exhaust sound sample (20260418) https://www.youtube.com/watch?v=wKeTXxwpkS0
- Brandon Collins - Pissed Off Going from Last to First - Spec Miata ABCC (20230809) https://www.youtube.com/watch?v=3Z5yoO60x_4
- Touge Terapy - Track POV - MX-5 NB | Vasco Sameiro Circuit (20241006) https://www.youtube.com/watch?v=4_5_lk5uQbc
- banpeinet - Mazda MX5 NB Super Bird [Down on the Street] (20160308) https://www.youtube.com/watch?v=XaYJHuqgYts
- Touge Terapy - Drift Wet Touge Uphill | MX-5 NB [POV] (20241012) https://www.youtube.com/watch?v=a4kX_e9rCs0
- Dover Labs - 1990 Miata Cold Start Magnaflow Cat and Borla Dual Exhaust Cold Start (20120413) https://www.youtube.com/watch?v=QtGJauSXC9s [octave pinned x1]
- MarcinGP - Mazda MX-5 (Miata) cold start / zimny rozruch (1) #shorts (20210126) https://www.youtube.com/watch?v=U8UsbgtuQA0 [octave pinned x1]
- MarcinGP - Mazda MX-5 (Miata) cold start / zimny rozruch (3) #shorts (20210128) https://www.youtube.com/watch?v=qVYVW9C8HQo [octave pinned x1]
- MarcinGP - Mazda MX-5 (Miata) cold start / zimny rozruch (2) #shorts (20210126) https://www.youtube.com/watch?v=uFjYN40w50g [octave pinned x1]

**`bmw_m20_i6`** (6)
- Old Man - E30 m20 amazing exhaust sound (20150502) https://www.youtube.com/watch?v=HRAfguZA4NY [octave pinned x1]
- Old Man - E30 m20 tunnel pure sound (20170521) https://www.youtube.com/watch?v=fnXZ4Tn1Uh0 [octave pinned x1]
- Old Man - E30 m20 tunnel sound , night (20170510) https://www.youtube.com/watch?v=oDad7Etf4eE [octave pinned x1]
- AUTO INSIGHTS KE - BMW E30 325i M20b25 amazing exhaust sound #bmw #bmwe30 #m20b25 #e30 (20241102) https://www.youtube.com/watch?v=3j_186SQb_c [octave pinned x1]
- Marjan_Z_BMW - BMW E30 327i M20B27  orginal sound (20220322) https://www.youtube.com/watch?v=CVH_ifxb37Q [octave pinned x1]
- Foot to Pedal - BMW E30 POV Country Road Drive | 1989 E30 320i Touring | Scorpion Exhaust Pure Sound (20210611) https://www.youtube.com/watch?v=-J5IxZUuwlI

**`twincam_i4_loud`** (5)
- Wishlist Project - 4age 16v ITB test running (20211127) https://www.youtube.com/watch?v=ZH4s9gxKErc [octave pinned x1]
- Driven Auto Enthusiasts - Toyota 4AGE sound compilation 1 ASMR (20210516) https://www.youtube.com/watch?v=_3kHos_9iwM [octave pinned x1]
- Luciano's Classics - 1987 Toyota MR2 AW11 Exhaust Sound (20241226) https://www.youtube.com/watch?v=FXQccDRSiMM [octave pinned x1]
- Tumyp ZAkadrom - 4A-GE sound silver top (20210803) https://www.youtube.com/watch?v=2H-5-IvYI6E [octave pinned x1]
- Wishlist Project - AE86 POV - Sungai Petani Version (20230629) https://www.youtube.com/watch?v=T6PevOGAJf0

**`ohv_v6`** (13)
- Luciano's Classics - 1988 Pontiac Fiero GT Walkaround, Startup and Sound (20260918) https://www.youtube.com/watch?v=tnSj38IeCfQ [octave pinned x1]
- Luciano's Classics - 1988 Pontiac Fiero GT Walkaround, Startup and Sound (short version) (20261022) https://www.youtube.com/watch?v=GRIS9mm51uE [octave pinned x1]
- James Barbour - FieroColdStart (20210613) https://www.youtube.com/watch?v=0IWsq_0YYsQ [octave pinned x1]
- Joshua Hasson - '96 Mustang, 3.8 new project (20130403) https://www.youtube.com/watch?v=Xl3PeqVa_H8 [octave pinned x1]
- mad monkey - 2003 Mazda Tribute |3.0 V6 197 HP| POV Test Drive (20211013) https://www.youtube.com/watch?v=xcuw8pFvPVk
- Brewton Garage - 1989 Chevy Beretta  3400 cold start and drive (20181016) https://www.youtube.com/watch?v=lpLcICHN_Zg
- Purple Wave - 2006 Ford Taurus SE for sale | sold at auction October 16, 2014 (20141008) https://www.youtube.com/watch?v=fOxndSFQW-E [octave pinned x1]
- Purple Wave - 2001 Ford Taurus LX for sale | sold at auction March 21, 2013 (20130228) https://www.youtube.com/watch?v=TmQvCVV4wbg [octave pinned x1]
- Purple Wave - 1996 Ford Taurus GL for sale | sold at auction March 21, 2013 (20130228) https://www.youtube.com/watch?v=kNtDfg8Th-s [octave pinned x1]
- HunteR82 - 1988 3.1 V6 Camaro vs 1991 V8 5.7 Caprice (1\4 mile) (20110709) https://www.youtube.com/watch?v=JDry3aTX3gM
- Late Night Auto Mods - Mustang V6 Drifting @ Club Loose - Pitt Race (20190926) https://www.youtube.com/watch?v=TQGEqGZBQwg
- Belal Qaradaxe - Mustang V6 Drifting training (20200423) https://www.youtube.com/watch?v=IIJZ4lr8bmE
- David Martin (DAVe3283) - 1998 Grand Prix GTP Drag Race (20190722) https://www.youtube.com/watch?v=Yw501dcl-aI

**`toyota_1jz_turbo`** (8)
- jamesmglover - Starting and idling with all the sensors wired in. (no down pipe) (20120902) https://www.youtube.com/watch?v=B2hZqvr9QrA [octave pinned x1]
- Light Touch Tuning - Kris 1JZ MA70 (20211029) https://www.youtube.com/watch?v=v_5Ge_essAE [octave pinned x1]
- Light Touch Tuning - Stock 1JZ Swapped MK3 SuPrA w/ECUmasters EMU Classic PnP (20211027) https://www.youtube.com/watch?v=RX5CdVro2TA [octave pinned x1]
- Bryant Takahashi - NIGHT DRIVE POV | 400HP 1JZGTE TOYOTA CHASER JZX100 (20250605) https://www.youtube.com/watch?v=aQrmJ_2wGg0
- Black Raven Motorsport - JZX100 Chaser's First Real Test on the Circuit (20171119) https://www.youtube.com/watch?v=Ev0W5xk1ZQ0
- JZX100K-sN 1JZ - 1JZ ドリフトミーティング　2016 3 (20161011) https://www.youtube.com/watch?v=QHAIpn4pGj0
- Turbulenzz - Markus Muller E46 1JZ Drift RAW - Nurburgring - TFB Media - pure sound (20160306) https://www.youtube.com/watch?v=zSaJLB7UUww [octave pinned x1]
- JZAirlines - Toyota Chaser JZX100 JZAirlines Drift trainig DSL 2018 st2 (20180703) https://www.youtube.com/watch?v=IWZzEfSHCRI

**`subaru_fa20_flat4`** (8)
- TheAverageDriver - Roller Coaster Roads in Adelaide Hills - POV Drive [Subaru BRZ] (20240812) https://www.youtube.com/watch?v=7qqj0yadN88
- TheAverageDriver - Chill Drive to the Beach - POV Drive [Subaru BRZ] (20240820) https://www.youtube.com/watch?v=yOvbnpeQ9JM
- David Mazary - FR-S Cold Start with Nameless track pipe and full exhaust (20161205) https://www.youtube.com/watch?v=tned3KSmjnU [octave pinned x1]
- Isaiah  - QUICK POV OF 2020 BRZ tS (20240826) https://www.youtube.com/watch?v=gwB-ZSZ16gA
- TheAverageDriver - First Drive in the Adelaide Hills - POV Drive [Subaru BRZ] (20240809) https://www.youtube.com/watch?v=UV9vrZqKw0I
- Touge Motorsports - Red Scion FRS - 2023.7.8 Touge.ca Cayuga TMP Track Event - 360 footage - GS010343 (20230816) https://www.youtube.com/watch?v=WeYIBR1Z-0Y
- Touge Motorsports - White Scion FRS footage @ 2024.8.5 Touge.ca Mosport DDT Track event  GS020501 (20240830) https://www.youtube.com/watch?v=4u_J_2aEc6o
- Touge Motorsports - White Scion FRS footage - 2024.7.1 Touge.ca Mosport DDT Track event - GS010481 (20240704) https://www.youtube.com/watch?v=6e9Sp--zUUM

**`vw_aircooled_flat4`** (6)
- Luciano's Classics - 1972 VW Beetle 1300 Walkaround, Startup & Sound (short version) (20260528) https://www.youtube.com/watch?v=eleSzd9bHsA [octave pinned x1]
- Jesse Mast - Jesse/DVK Volkswagen '64 - 2176cc (20110628) https://www.youtube.com/watch?v=NLbnvS1_GrY [octave pinned x1]
- Southern Fried Autocross - VW Bug 1679cc (20140419) https://www.youtube.com/watch?v=wSLjeGppjB0 [octave pinned x1]
- yellowdcap - First idle in 5 years (20120108) https://www.youtube.com/watch?v=Ff5o02IoKBI [octave pinned x1]
- trucksplususayakima - 1972 Volkswagen Beetle Karmann Covertible (20111103) https://www.youtube.com/watch?v=ofyUOGh0EoI [octave pinned x1]
- SCAT VW - Orange #VW Bug Engine | Luis A. Dominguez (20221017) https://www.youtube.com/watch?v=nD-PWaX1Cn8 [octave pinned x1]

**`mini_supercharged_i4`** (6)
- Xantix - CRUISE IN MINI R53 [POV] (20240331) https://www.youtube.com/watch?v=h4KMYYr3hl8
- Torvek Motors - POV Drive On The Mini Cooper S To Pick Up New Parts (20210404) https://www.youtube.com/watch?v=6WJga9j35f8
- IvoJan - MINI Cooper S R53 2004 with jetex fortex exhaust (20120417) https://www.youtube.com/watch?v=8p8kQ1vOc00 [octave pinned x1]
- FlorisDiemel - Mini R53 PlayMini exhaust (20110717) https://www.youtube.com/watch?v=pTD7ikh9nzc [octave pinned x1]
- FlorisDiemel - PlayMini exhaust on R53 (20110723) https://www.youtube.com/watch?v=zJnHRC5AZpM [octave pinned x1]
- MC - Mini John Cooper Works GP r53. Exhaust sound, acceleration and flat out. (Pure car sound) (20131124) https://www.youtube.com/watch?v=EC0shmCAyzg [octave pinned x1]


`credits.json` rebuilt from the engine.json sources (`make_credits.py`); `index.json` `real_bins` refreshed. Three
round-one sources failed to download once (a transient yt-dlp n-challenge error) and were fetched on retry; every family
in the final build has all its listed sources.

## The game-side change: ShiftDrop (`src/app/audio-field.ts`, `src/app/modes/race.ts`)

An opt-in shaping of the rpm an `EngineVoice` plays (`VoiceOptions.shiftDrop`, `FieldOptions.shiftDrop`, off by
default, so without it the voice plays the physics rpm exactly as before). On a gear increment the played rpm leaves
the physics rpm and falls with a 50 ms time constant to the landing rpm: the road-speed clutch-side rpm in the new gear
(speed / wheel radius x the gear's overall ratio, `boxRpm`) times the wheel slip the engine ran at before the shift. It
never goes above the physics rpm, rejoins it within 2 %, or blends back (100 ms) after 1.0 s; downshifts (the blips)
are untouched. The on / off crossfade is unchanged: the 0.15 s torque cut brings the off layer up within its 70 ms lag
while the note falls, and the new gear pulls on the on layer. Race mode turns it on for the AI field and passes each
car's gear and `boxRpm` (`boxRpmOf`, from `dir.cars[i].spec`, app code only; no physics or AI change). Measured on the
physics (90 % of the drop): #38 2->3 0.60 s physics / 0.03 s played, 3->4 0.47 / 0.07, 4->5 0.43 / 0.08; #41 1->2
0.42 / 0.08, 2->3 0.42 / 0.10. **The Probe's CarAudio is unchanged (byte-identical).** The owner's own set is affected
the same way by the physics (1->2 0.77 s, 2->3 0.45 s, 3->4 0.45 s; ShiftDrop would make them 0.05-0.08 s), but he
heard it as OK, so it is left for him to decide. Test: `src/app/__tests__/audio-shift.test.ts` (9 tests: ShiftDrop
against the physics of #38, #41 and the Probe, edge cases, the race-mode wiring, EngineVoice with and without the option).

## The clips (`tools/audio/chain/`)

Rendered through the game's real chain: `render_chain.ts` bundles `entry.ts` with esbuild, serves public/ locally and
runs the game's `EngineVoice` (AI families: trim 1, muffler 0.3, shiftDrop on, the scenario's gear and clutch-side rpm)
or the player's `CarAudio` (`mazda_kl_v6`) in an OfflineAudioContext in headless Chrome, updated at 60 Hz as the race
mode does (seeded Math.random). The scenario is round one's (`scenario.py`). **Loudness-matched**: every clip has the
same A-weighted RMS over its 25 s (LAeq -30.4 dBFS), the highest common level at which every peak stays at or under
-1 dBFS; no limiter. MP3 128 kbps 48 kHz mono, in `tmp/sound_demo2/clips/` with `clips.json` (raw LAeq, gain, peak).
The page `tmp/sound_demo2/index.html` ("Engine Listening Room 2") quotes his round-one note on each card with what it
traced to, what changed, and what is still weak; the notes boxes and the db script are round one's.

## Still weak

1. **Off-throttle layers are thin on real recordings.** A 1 s overrun stretch inside the pitch window is rare in
   onboard footage, so many off bins are the on loop at its own pitch, darkened (`from-on`): `classic_v8_lowrev` 11 of
   19, `modern_i4_stock` 2. No squeak (no upward shift beyond x1.18), but a lift may sound like a quieter pull.
2. **Idles.** No real idle inside the window for `mazda_b_i4` (850), `ohv_v6` (700), `mini_supercharged_i4` (800):
   the clips found idle at 1000-1150 rpm (cold or high idle), and the family idle values are lower than any recording.
3. **Low on-throttle bins** (750-1500 rpm) still pitch-shifted past the window in `vintage_i6`, `ohv_v6`,
   `mazda_b_i4`, `gm_sbc_v8` (x1.143 against 1.14).
4. **Seams**: 1 s loops and joined segments have lower seam correlation than round one's short loops in five
   families (above). Listen for a soft once-a-second repeat.
5. The V8 octave: double-speed tracking fixed the contrast, but whole V8 sources still rest on the per-source octave
   rule; the rev clips are pinned x1.
6. The speech detector is Silero; it cannot hear music. Sources with music beds would pass.
7. `sohc_i4_loud` and `mazda_kl_v6` keep their round-one loops (0.48 / 0.85 s, pitched idles), by the owner's ear.

## Machine notes

Battery 75-100 % throughout (briefly discharging), load average 2-4, one heavy process at a time. Disk dipped to 9.4 GB
free mid-run; `uv cache prune` and dropping each family's FLACs after its build kept it above 10 GB afterwards; the audio
cache ends at about 0.6 GB (rpm, idle and speech tracks; no FLACs).
