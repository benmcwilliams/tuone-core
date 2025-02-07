```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "PSG-Marine-&-Logistics-Ltd" or company = "PSG Marine & Logistics Ltd")
sort location, dt_announce desc
```
