```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "EVSE-(Energieversorgung-Schwerin-GmbH-&-Co.-Erzeugung-KG)" or company = "EVSE (Energieversorgung Schwerin GmbH & Co. Erzeugung KG)")
sort location, dt_announce desc
```
