```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and company = "Centrosolar Glas GmbH & Co. KG"
sort location, dt_announce desc
```
