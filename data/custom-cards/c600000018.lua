--SPDX-License-Identifier: AGPL-3.0-or-later
--Machina Peacekeeper (historical implementation, Retro Formats)
--Upstream: https://github.com/ProjectIgnis/CardScripts/blob/383bfbd62cefc0a28e075acfb78b0bb8203b94c7/official/c78349103.lua
--Copyright (C) 2020  Project Ignis contributors. See version history and author credit line for each file.
--Modified by edopro-retro-formats on 2026-09-29: a monster can only be equipped with 1 Union monster at a time, as the period text prints it as a Condition (the equip effect is offered only for a monster carrying no Union monster, and the card counts as an old-rule Union for other Union cards' equip checks; proc_union.lua's procedure is written out in the script with Auxiliary.UnionTarget's old rule); the effect description is read from the modern card's strings.
--This modified file is licensed, like its upstream, under the GNU Affero General
--Public License, version 3 or (at your option) any later version. The licence
--text is LICENSE-AGPL-3.0-or-later.txt next to this file in dist/scripts/, and
--LICENSES/AGPL-3.0-or-later.txt in the edopro-retro-formats repository.
--
--Period text: "When this card on the field is destroyed and sent to the Graveyard, you can add 1
--Union Monster from your Deck to your hand. Once per turn, during your Main Phase, you
--can equip this card to a Machine-Type monster you control as an Equip Card, OR unequip
--it to Special Summon this card in face-up Attack Position. (A monster can only be
--equipped with 1 Union Monster at a time. If the equipped monster would be destroyed,
--destroy this card instead.)"
--
--See data/custom-cards/c600000018.json for what this script does not reproduce.
--マシンナーズ・ピースキーパー
--Machina Peacekeeper
local s,id=GetID()
--Project Ignis's Auxiliary.AddUnionProcedure (proc_union.lua) for a Union monster under the
--current rules (oldequip and oldprotect both false), except for the period Condition "A monster
--can only be equipped with 1 Union monster at a time": the equip effect uses the old rule of
--Auxiliary.UnionTarget (a monster carrying any Union monster is not a legal target), and the card
--is marked old_union so that other Union cards' equip checks count it as well. The unequip
--position and the destruction substitute stay as the current procedure has them.
function s.AddUnionProcedure(c,f)
	--equip
	local e1=Effect.CreateEffect(c)
	e1:SetDescription(1068)
	e1:SetCategory(CATEGORY_EQUIP)
	e1:SetProperty(EFFECT_FLAG_CARD_TARGET)
	e1:SetType(EFFECT_TYPE_IGNITION)
	e1:SetRange(LOCATION_MZONE)
	e1:SetTarget(Auxiliary.UnionTarget(f,true))
	e1:SetOperation(Auxiliary.UnionOperation(f))
	c:RegisterEffect(e1)
	--unequip
	local e2=Effect.CreateEffect(c)
	e2:SetDescription(2)
	e2:SetCategory(CATEGORY_SPECIAL_SUMMON)
	e2:SetType(EFFECT_TYPE_IGNITION)
	e2:SetRange(LOCATION_SZONE)
	e2:SetCondition(function(e) return e:GetHandler():GetEquipTarget() end)
	e2:SetTarget(Auxiliary.UnionSumTarget(false))
	e2:SetOperation(Auxiliary.UnionSumOperation(false))
	c:RegisterEffect(e2)
	--destroy sub
	local e3=Effect.CreateEffect(c)
	e3:SetType(EFFECT_TYPE_EQUIP)
	e3:SetProperty(EFFECT_FLAG_IGNORE_IMMUNE)
	e3:SetCode(EFFECT_DESTROY_SUBSTITUTE)
	e3:SetCondition(function(e) return e:GetHandler():GetEquipTarget() end)
	e3:SetValue(Auxiliary.UnionReplace(false))
	c:RegisterEffect(e3)
	--eqlimit
	local e4=Effect.CreateEffect(c)
	e4:SetType(EFFECT_TYPE_SINGLE)
	e4:SetCode(EFFECT_UNION_LIMIT)
	e4:SetProperty(EFFECT_FLAG_CANNOT_DISABLE)
	e4:SetValue(Auxiliary.UnionLimit(f))
	c:RegisterEffect(e4)
	c:GetMetatable().old_union=true
end
function s.initial_effect(c)
	s.AddUnionProcedure(c,aux.FilterBoolFunction(Card.IsRace,RACE_MACHINE))
	--search
	local e1=Effect.CreateEffect(c)
	e1:SetDescription(aux.Stringid(78349103,2))
	e1:SetCategory(CATEGORY_TOHAND+CATEGORY_SEARCH)
	e1:SetType(EFFECT_TYPE_TRIGGER_O+EFFECT_TYPE_SINGLE)
	e1:SetProperty(EFFECT_FLAG_DAMAGE_STEP)
	e1:SetCode(EVENT_TO_GRAVE)
	e1:SetCondition(s.scon)
	e1:SetTarget(s.stg)
	e1:SetOperation(s.sop)
	c:RegisterEffect(e1)
end
function s.sfilter(c)
	return c:IsType(TYPE_UNION) and c:IsAbleToHand()
end
function s.scon(e,tp,eg,ep,ev,re,r,rp)
	return e:GetHandler():IsPreviousLocation(LOCATION_ONFIELD) and e:GetHandler():IsReason(REASON_DESTROY)
end
function s.stg(e,tp,eg,ep,ev,re,r,rp,chk)
	if chk==0 then return Duel.IsExistingMatchingCard(s.sfilter,tp,LOCATION_DECK,0,1,nil) end
	Duel.SetOperationInfo(0,CATEGORY_TOHAND,nil,1,tp,LOCATION_DECK)
end
function s.sop(e,tp,eg,ep,ev,re,r,rp)
	Duel.Hint(HINT_SELECTMSG,tp,HINTMSG_ATOHAND)
	local g=Duel.SelectMatchingCard(tp,s.sfilter,tp,LOCATION_DECK,0,1,1,nil)
	if #g>0 then
		Duel.SendtoHand(g,nil,REASON_EFFECT)
		Duel.ConfirmCards(1-tp,g)
	end
end