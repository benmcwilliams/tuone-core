```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "EST-Energie-&-Solar-Technik" or company = "EST Energie & Solar Technik")
sort location, dt_announce desc
```
