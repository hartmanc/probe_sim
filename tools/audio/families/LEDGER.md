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
