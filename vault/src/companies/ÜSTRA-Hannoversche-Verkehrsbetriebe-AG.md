```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "ÜSTRA-Hannoversche-Verkehrsbetriebe-AG" or company = "ÜSTRA Hannoversche Verkehrsbetriebe AG")
sort location, dt_announce desc
```
