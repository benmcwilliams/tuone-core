```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and company = "North Sea OFW N12 1 GmbH & Co. KG"
sort location, dt_announce desc
```
